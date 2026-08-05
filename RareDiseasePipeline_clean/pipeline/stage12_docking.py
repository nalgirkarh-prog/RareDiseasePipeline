from modules.receptor_preparer import ReceptorPreparer
from modules.ligand_preparer import LigandPreparer
from modules.pocket_geometry import PocketGeometry
from clients.vina import VinaClient


class DockingStage:

    def __init__(self):

        self.receptor = ReceptorPreparer()

        self.ligand = LigandPreparer()

        self.geometry = PocketGeometry()

        self.vina = VinaClient()

    def run(
        self,
        pdb_file,
        pocket,
        ligands
    ):
        receptor = self.receptor.prepare(
            pdb_file.file_path
        )

        box = self.geometry.calculate(
            pocket.source_file.replace(
                "_atm.pdb",
                "_vert.pqr"
            )
        )

        # Group ligands into 3 sets of 10
        sets = [
            ligands[0:10],
            ligands[10:20],
            ligands[20:30]
        ]
        sets = [s for s in sets if s]

        all_docked_results = []
        valid_candidates = []

        print(f"\n=======================================================")
        print(f"▶ Starting Sequential Docking Filter (Target score <= -7.0 kcal/mol)")
        print(f"=======================================================\n")

        for set_idx, ligand_set in enumerate(sets, start=1):
            print(f"--- Evaluating Set {set_idx}/{len(sets)} ({len(ligand_set)} ligands) ---")
            set_results = []

            for i, ligand in enumerate(ligand_set, start=1):
                print(f"[{i}/{len(ligand_set)}] Docking {ligand.name}...")

                try:
                    ligand_file = self.ligand.prepare(ligand)
                    result = self.vina.dock(
                        receptor,
                        ligand_file,
                        box
                    )

                    result["ligand"] = ligand
                    result["ligand_name"] = ligand.name
                    result["smiles"] = ligand.smiles
                    result["mw"] = ligand.molecular_weight
                    result["logp"] = ligand.logp
                    result["hbd"] = ligand.hbd
                    result["hba"] = ligand.hba
                    result["rotatable_bonds"] = ligand.rotatable_bonds

                    set_results.append(result)
                    all_docked_results.append(result)

                except Exception as e:
                    print(f"   ❌ Error docking {ligand.name}: {e}")

            # Check if any ligand in this set has docking score <= -7.0 kcal/mol
            qualifying = [
                r for r in set_results
                if r.get("affinity") is not None and r["affinity"] <= -7.0
            ]

            if qualifying:
                print(f"\n✅ Set {set_idx} HAS {len(qualifying)} ligand(s) with docking score <= -7.0 kcal/mol!")
                # Accumulate qualifying ligands across all sets
                valid_candidates.extend(qualifying)
            else:
                print(f"\n⚠️ Set {set_idx} has NO ligand with docking score <= -7.0 kcal/mol.")
                if set_idx < len(sets):
                    print(f"Proceeding to Set {set_idx + 1}...\n")

        if not valid_candidates:
            print("\n⚠️ None of the sets produced a ligand with docking score <= -7.0 kcal/mol.")
            if all_docked_results:
                # Fallback: select ligand with most negative affinity across all results
                all_docked_results.sort(
                    key=lambda x: x["affinity"] if x.get("affinity") is not None else 999
                )
                lowest = all_docked_results[0]
                print(f"📌 Fallback: Selecting candidate with lowest docking score: {lowest['ligand_name']} ({lowest['affinity']:.2f} kcal/mol)\n")
                valid_candidates = [lowest]
            else:
                print("❌ No docking results obtained across any set.\n")
                return []

        # At this point, valid_candidates contains all ligands meeting the <= -7.0 threshold (or the fallback one).
        # Sort by affinity (most negative first) and break ties using 'energy' if present.
        valid_candidates.sort(
            key=lambda x: (
                x["affinity"] if x.get("affinity") is not None else 999,
                x.get("energy", 0)
            )
        )

        # Return the top-ranked candidate as a single-element list for downstream compatibility.
        return [valid_candidates[0]]


