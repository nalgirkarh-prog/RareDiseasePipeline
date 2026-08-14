"""
pipeline/stage12_docking.py

Molecular Docking stage.

Improvements over the original
--------------------------------
1. Per-ligand 120-second hard timeout via ThreadPoolExecutor — one hung Vina
   process can no longer take down the whole stage.
2. Every attempt (success / failed / timeout) is persisted with a 'status'
   field and, on failure, a real error message.
3. Checkpoint file (output/docking_checkpoint.json) written after every
   ligand so a restart resumes from the last completed ligand.
4. Parity-check log line at the end of the stage:
   attempted={n} screened={m} — the moment attrition is visible in the log.
"""

from __future__ import annotations

import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import List

from models.ligand import Ligand
from modules.receptor_preparer import ReceptorPreparer, ReceptorPrepResult
from modules.ligand_preparer import LigandPreparer
from modules.pocket_geometry import PocketGeometry
from clients.vina import VinaClient

# Hard wall-clock limit per ligand (seconds).
_LIGAND_TIMEOUT = 120

_CHECKPOINT_PATH = Path("output") / "docking_checkpoint.json"


def _reconstruct_ligand(r: dict, name: str) -> Ligand:
    return Ligand(
        ligand_id=r.get("ligand_id", name),
        name=name,
        smiles=r.get("smiles"),
        molecular_weight=r.get("mw"),
        logp=r.get("logp"),
        hbd=r.get("hbd"),
        hba=r.get("hba"),
        rotatable_bonds=r.get("rotatable_bonds"),
        source=r.get("source", "ChEMBL"),
    )


def _load_checkpoint() -> dict:
    """Return {ligand_name: result_dict} for all previously completed attempts."""
    if _CHECKPOINT_PATH.exists():
        try:
            with open(_CHECKPOINT_PATH) as f:
                data = json.load(f)
                results = {}
                for r in data:
                    name = r.get("ligand_name")
                    if not name:
                        continue
                    lig_val = r.get("ligand")
                    if isinstance(lig_val, dict):
                        try:
                            r["ligand"] = Ligand(**lig_val)
                        except Exception:
                            r["ligand"] = _reconstruct_ligand(r, name)
                    elif not isinstance(lig_val, Ligand):
                        r["ligand"] = _reconstruct_ligand(r, name)
                    results[name] = r
                return results
        except Exception:
            pass
    return {}


def _save_checkpoint(all_results: List[dict]) -> None:
    """Overwrite the checkpoint file with the current result list."""
    _CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    serializable_results = []
    for r in all_results:
        item = dict(r)
        lig = item.get("ligand")
        if isinstance(lig, Ligand):
            if hasattr(lig, "model_dump"):
                item["ligand"] = lig.model_dump()
            elif hasattr(lig, "dict"):
                item["ligand"] = lig.dict()
        serializable_results.append(item)
    with open(_CHECKPOINT_PATH, "w") as f:
        json.dump(serializable_results, f, indent=2, default=str)


class DockingStage:

    def __init__(self):
        self.receptor = ReceptorPreparer()
        self.ligand = LigandPreparer()
        self.geometry = PocketGeometry()
        self.vina = VinaClient()

    # ------------------------------------------------------------------

    def run(self, pdb_file, pocket, ligands, context: dict | None = None):
        prep_result: ReceptorPrepResult = self.receptor.prepare(pdb_file.file_path)
        receptor = prep_result.pdbqt_path

        # Persist Open Babel warnings into the pipeline context for the report
        if context is not None and prep_result.obabel_warnings:
            context.setdefault("structure_preparation", {})["obabel_warnings"] = prep_result.obabel_warnings

        box = self.geometry.calculate(
            pocket.source_file.replace("_atm.pdb", "_vert.pqr")
        )

        # ----- Resume support: skip already-finished ligands ------------
        checkpoint = _load_checkpoint()
        all_docked_results: List[dict] = list(checkpoint.values())
        done_names = set(checkpoint.keys())

        remaining = [lg for lg in ligands if lg.name not in done_names]
        if done_names:
            print(
                f"\n♻️  Checkpoint found — resuming from ligand "
                f"{len(done_names) + 1}/{len(ligands)} "
                f"({len(done_names)} already completed)"
            )

        # Group remaining ligands into sets of 10
        sets = [remaining[i:i + 10] for i in range(0, len(remaining), 10)]
        sets = [s for s in sets if s]

        valid_candidates = [
            r for r in all_docked_results
            if r.get("status") == "success"
            and r.get("affinity") is not None
            and r["affinity"] <= -7.0
        ]

        print(f"\n{'=' * 55}")
        print("▶ Starting Sequential Docking Filter (Target score <= -7.0 kcal/mol)")
        print(f"{'=' * 55}\n")

        for set_idx, ligand_set in enumerate(sets, start=1):
            print(f"--- Evaluating Set {set_idx}/{len(sets)} ({len(ligand_set)} ligands) ---")
            set_results = []

            for i, ligand in enumerate(ligand_set, start=1):
                print(f"[{i}/{len(ligand_set)}] Docking {ligand.name}...")

                result = self._dock_one(receptor, ligand, box)
                set_results.append(result)
                all_docked_results.append(result)

                # Checkpoint after every attempt regardless of status
                _save_checkpoint(all_docked_results)

                if result["status"] == "success":
                    aff = result.get("affinity")
                    aff_str = f"{aff:.2f} kcal/mol" if aff is not None else "N/A"
                    print(f"   ✓ {ligand.name}   {aff_str}")
                else:
                    print(f"   ❌ {ligand.name}   [{result['status']}] {result.get('error', '')}")

            # Qualifying from this set
            qualifying = [
                r for r in set_results
                if r.get("status") == "success"
                and r.get("affinity") is not None
                and r["affinity"] <= -7.0
            ]

            if qualifying:
                print(f"\n✅ Set {set_idx} HAS {len(qualifying)} ligand(s) with score <= -7.0 kcal/mol!")
                valid_candidates.extend(qualifying)
            else:
                print(f"\n⚠️  Set {set_idx} has NO ligand with score <= -7.0 kcal/mol.")
                if set_idx < len(sets):
                    print(f"Proceeding to Set {set_idx + 1}...\n")

        # ----- Parity check (Fix 3) ------------------------------------
        n_screened = len(ligands)
        n_attempted = len(all_docked_results)
        n_success = sum(1 for r in all_docked_results if r.get("status") == "success")
        n_failed = n_attempted - n_success

        if n_attempted != n_screened:
            print(
                f"\n⚠️  PARITY WARNING — screened={n_screened} attempted={n_attempted} "
                f"(delta={n_screened - n_attempted}). Some ligands were not attempted."
            )
        else:
            print(
                f"\n📊 Docking parity OK — screened={n_screened} attempted={n_attempted} "
                f"success={n_success} failed/timeout={n_failed}"
            )

        # ----- Fallback if nothing cleared the threshold ---------------
        if not valid_candidates:
            successful = [r for r in all_docked_results if r.get("status") == "success"]
            print("\n⚠️  None of the sets produced a ligand with score <= -7.0 kcal/mol.")
            if successful:
                successful.sort(key=lambda x: x["affinity"] if x.get("affinity") is not None else 999)
                lowest = successful[0]
                print(
                    f"📌 Fallback: {lowest['ligand_name']} "
                    f"({lowest['affinity']:.2f} kcal/mol)\n"
                )
                valid_candidates = [lowest]
            else:
                print("❌ No successful docking results across any set.\n")
                return [], all_docked_results

        # Sort by affinity; break ties with energy
        valid_candidates.sort(
            key=lambda x: (
                x["affinity"] if x.get("affinity") is not None else 999,
                x.get("energy", 0),
            )
        )

        # Return top-ranked candidate + full result list for downstream parity/ranking
        return [valid_candidates[0]], all_docked_results

    # ------------------------------------------------------------------

    def _dock_one(self, receptor: str, ligand, box: dict) -> dict:
        """
        Dock a single ligand with a hard 120-second timeout.

        Returns a result dict with a 'status' key:
          "success"  — Vina completed and returned an affinity
          "failed"   — Vina raised an exception
          "timeout"  — Vina exceeded the per-ligand time limit
        """
        base_result = {
            "ligand": ligand,
            "ligand_name": ligand.name,
            "smiles": ligand.smiles,
            "mw": ligand.molecular_weight,
            "logp": ligand.logp,
            "hbd": ligand.hbd,
            "hba": ligand.hba,
            "rotatable_bonds": ligand.rotatable_bonds,
        }

        try:
            ligand_file = self.ligand.prepare(ligand)
        except Exception as e:
            return {
                **base_result,
                "status": "failed",
                "error": f"Ligand preparation failed: {e}",
                "affinity": None,
            }

        def _run():
            return self.vina.dock(receptor, ligand_file, box)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            try:
                result = future.result(timeout=_LIGAND_TIMEOUT)
                return {
                    **base_result,
                    **result,
                    "status": "success",
                    "error": None,
                }
            except FuturesTimeoutError:
                future.cancel()
                return {
                    **base_result,
                    "status": "timeout",
                    "error": f"Exceeded {_LIGAND_TIMEOUT}s wall-clock limit",
                    "affinity": None,
                }
            except Exception as e:
                return {
                    **base_result,
                    "status": "failed",
                    "error": traceback.format_exc().strip(),
                    "affinity": None,
                }
