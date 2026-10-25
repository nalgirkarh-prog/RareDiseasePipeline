"""
modules/ligand_discovery.py

Fix 1 (per-target ligand cap):
    The previous implementation issued `break` on both the inner activity loop
    and the outer target loop as soon as 30 total ligands had been collected.
    This meant that one high-yield target (typically the top-ranked STRING
    interactor) could exhaust the entire budget before any other target was
    ever queried, producing a biased, single-target ligand set.

    The fix allocates a per-target budget of ceil(GLOBAL_CAP / max_targets)
    ligands and applies that cap independently inside each target's activity
    loop.  The outer loop continues until all ranked targets have been queried
    or the global cap is reached.  A per-target summary line is logged so the
    source distribution is visible in run logs.
"""

import math
from collections import OrderedDict

from clients.chembl import ChEMBLClient
from models.ligand import Ligand

# Hard global cap: 5 docking sets × 10 ligands each.
GLOBAL_LIGAND_CAP = 50


class LigandDiscovery:

    def __init__(self):
        self.chembl = ChEMBLClient()

    def discover(
        self,
        interactions,
        min_confidence=0.70,
        max_targets=10,
        activity_limit=1000,
        primary_gene=None
    ):
        """
        Discover ligands from ChEMBL using the primary gene target and
        STRING interaction partners.

        Parameters
        ----------
        interactions  : list[Interaction]
        min_confidence: float  — minimum STRING confidence score
        max_targets   : int    — maximum number of STRING partners to query
        activity_limit: int    — ChEMBL activity records fetched per target
                                 (server-side limit before local filtering)
        primary_gene  : object | str | None
                        The primary gene target.  When provided its symbol is
                        queried in ChEMBL *before* STRING partners so that the
                        actual gene of interest always contributes ligands.

        Returns
        -------
        list[Ligand]  — up to GLOBAL_LIGAND_CAP unique ligands, sourced from
                        the primary gene target and as many ranked STRING
                        targets as have ChEMBL activity.
        """

        ligands: OrderedDict = OrderedDict()

        # ── 0. Query the PRIMARY gene target in ChEMBL first ──────────────
        primary_count = 0
        if primary_gene is not None:
            symbol = getattr(primary_gene, 'symbol', primary_gene)
            print(f"\n── Primary target ligands ──")
            print(f"Querying ChEMBL for primary gene target: {symbol}")

            try:
                search = self.chembl.search_target(symbol)
                if search.get("targets"):
                    chembl_id = search["targets"][0]["target_chembl_id"]
                    print(f"Primary target ChEMBL ID: {chembl_id}")

                    activities = self.chembl.get_activities(
                        chembl_id, limit=activity_limit
                    )

                    for activity in activities.get("activities", []):
                        if primary_count >= 15:
                            break

                        smiles = activity.get("canonical_smiles")
                        if not smiles:
                            continue

                        molecule = activity.get("molecule_chembl_id")
                        if molecule in ligands:
                            continue

                        try:
                            details = self.chembl.get_molecule(molecule)
                        except Exception:
                            continue

                        props = details.get("molecule_properties", {})

                        ligand = Ligand(
                            ligand_id=molecule,
                            name=(
                                details.get("pref_name")
                                or details.get("molecule_chembl_id")
                                or molecule
                            ),
                            smiles=smiles,
                            molecular_weight=float(
                                props.get("full_mwt") or 0
                            ),
                            logp=float(props.get("alogp") or 0),
                            hba=int(props.get("hba") or 0),
                            hbd=int(props.get("hbd") or 0),
                            rotatable_bonds=int(props.get("rtb") or 0),
                            source="ChEMBL",
                        )

                        ligands[molecule] = ligand
                        primary_count += 1

                    print(
                        f"  → {primary_count} ligand(s) from primary target "
                        f"{symbol}"
                    )
                else:
                    print(f"  No ChEMBL targets found for {symbol}")
            except Exception:
                print(f"  Failed to query ChEMBL for primary target {symbol}")

        # ── 1. Rank and filter STRING interactors ──────────────────────────
        ranked = sorted(interactions, key=lambda x: x.score, reverse=True)

        targets = []
        for interaction in ranked:
            if interaction.score < min_confidence:
                continue
            targets.append(interaction.protein)
            if len(targets) >= max_targets:
                break

        remaining_budget = GLOBAL_LIGAND_CAP - len(ligands)
        print(f"\n── STRING partner ligands ──")
        print(
            f"Searching ChEMBL for {len(targets)} STRING partners "
            f"(remaining budget: {remaining_budget})..."
        )

        # ── 2. Per-target cap prevents any single target from monopolising
        #       the ligand budget (Fix 1). ─────────────────────────────────
        per_target_cap = math.ceil(
            remaining_budget / max(len(targets), 1)
        )

        for target in targets:

            if len(ligands) >= GLOBAL_LIGAND_CAP:
                break  # global hard-stop; shouldn't normally be needed here

            print(f"\nTarget: {target}  (per-target cap: {per_target_cap})")

            try:
                search = self.chembl.search_target(target)
            except Exception:
                continue

            if not search.get("targets"):
                continue

            chembl_id = search["targets"][0]["target_chembl_id"]
            print(f"Target ID: {chembl_id}")

            try:
                activities = self.chembl.get_activities(
                    chembl_id,
                    limit=activity_limit
                )
            except Exception:
                continue

            target_count_before = len(ligands)

            for activity in activities.get("activities", []):

                # per-target cap: move to the next target once filled
                if len(ligands) - target_count_before >= per_target_cap:
                    break

                # global hard-stop
                if len(ligands) >= GLOBAL_LIGAND_CAP:
                    break

                smiles = activity.get("canonical_smiles")
                if not smiles:
                    continue

                molecule = activity.get("molecule_chembl_id")
                if molecule in ligands:
                    continue

                try:
                    details = self.chembl.get_molecule(molecule)
                except Exception:
                    continue

                props = details.get("molecule_properties", {})

                ligand = Ligand(
                    ligand_id=molecule,
                    name=(
                        details.get("pref_name")
                        or details.get("molecule_chembl_id")
                        or molecule
                    ),
                    smiles=smiles,
                    molecular_weight=float(props.get("full_mwt") or 0),
                    logp=float(props.get("alogp") or 0),
                    hba=int(props.get("hba") or 0),
                    hbd=int(props.get("hbd") or 0),
                    rotatable_bonds=int(props.get("rtb") or 0),
                    source="ChEMBL",
                )

                ligands[molecule] = ligand

            collected_from_target = len(ligands) - target_count_before
            print(
                f"  → {collected_from_target} ligand(s) from {target} "
                f"(running total: {len(ligands)})"
            )

        print(f"\nUnique ligands discovered: {len(ligands)}")
        return list(ligands.values())
