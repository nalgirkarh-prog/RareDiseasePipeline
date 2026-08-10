"""
pipeline/stage13_ranking.py

Candidate Ranking stage.

Improvements over the original
--------------------------------
- Accepts the new (candidates, all_results) tuple returned by DockingStage.run().
- Filters on status="success" before ranking; logs how many failed/timeout
  entries are being excluded.
- Persists the full result list (including failed/timeout) to
  output/docking_all_results.json for post-mortem analysis.
"""

from __future__ import annotations

from pathlib import Path
import csv
import json


class DockingRankingStage:

    def run(self, context):
        print("▶ Ranking docked ligands")

        raw = context.get("docking_results", [])

        # Unpack (candidates, all_results) tuple if DockingStage returned both.
        if isinstance(raw, tuple) and len(raw) == 2:
            candidates, all_results = raw
        else:
            # Legacy: raw is already the flat list of docked results
            candidates = raw if isinstance(raw, list) else []
            all_results = candidates

        # ---------- Save full result set for diagnostics ----------
        self._save_all_results(all_results)

        # ---------- Filter to successful docks only ---------------
        successful = [
            r for r in all_results
            if r.get("status") == "success" and r.get("affinity") is not None
        ]
        skipped = len(all_results) - len(successful)
        if skipped:
            print(
                f"   ⚠️  {skipped} ligand(s) excluded from ranking "
                f"(failed or timed out) — see output/docking_all_results.json"
            )

        # ---------- Rank ----------------------------------------
        ranked = sorted(successful, key=lambda x: x["affinity"])

        self._save_csv(ranked)
        self._save_json(ranked)

        context["ranked_candidates"] = ranked
        print(f"✓ Ranked {len(ranked)} ligands")

        return ranked

    # ------------------------------------------------------------------

    def _save_all_results(self, results: list) -> None:
        """Persist every attempt (success/failed/timeout) for post-mortem."""
        Path("output").mkdir(exist_ok=True)

        serialisable = []
        for r in results:
            row = {k: v for k, v in r.items() if k != "ligand"}
            # Ensure ligand_name is always present
            if "ligand_name" not in row and "ligand" in r:
                row["ligand_name"] = getattr(r["ligand"], "name", str(r["ligand"]))
            serialisable.append(row)

        with open("output/docking_all_results.json", "w") as f:
            json.dump(serialisable, f, indent=4, default=str)

    # ------------------------------------------------------------------

    def _save_csv(self, results: list) -> None:
        Path("output").mkdir(exist_ok=True)

        with open("output/docking_ranking.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Ligand", "Affinity", "Status"])
            for item in results:
                ligand_name = item.get("ligand_name") or getattr(
                    item.get("ligand"), "name", "unknown"
                )
                writer.writerow([ligand_name, item["affinity"], item.get("status", "success")])

    # ------------------------------------------------------------------

    def _save_json(self, results: list) -> None:
        output = []
        for item in results:
            ligand_name = item.get("ligand_name") or getattr(
                item.get("ligand"), "name", "unknown"
            )
            output.append({
                "ligand": ligand_name,
                "affinity": item["affinity"],
                "status": item.get("status", "success"),
            })

        with open("output/docking_ranking.json", "w") as f:
            json.dump(output, f, indent=4)
