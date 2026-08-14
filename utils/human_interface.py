"""
utils/human_interface.py

Human-in-the-Loop Research Interface for RareDiseasePipeline.

Enables interactive human decision-making:
1. Selective Pipeline Execution Depth (stop at any target stage).
2. Protein Structure Override (choose custom PDB ID or local PDB file from literature).
3. Custom Ligand Literature Input (add/override SMILES or drug candidates before docking).

Author: Harsh Nalgirkar
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from models.ligand import Ligand
from models.structure import Structure


def helper_parse_smiles_to_ligand(name: str, smiles: str, ligand_id: Optional[str] = None) -> Optional[Ligand]:
    """
    Parse a SMILES string into a Ligand object with properties calculated via RDKit.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, Lipinski

        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            print(f"  ❌ Invalid SMILES string: '{smiles}'")
            return None

        canonical_smiles = Chem.MolToSmiles(mol)
        mw = float(Descriptors.MolWt(mol))
        logp = float(Descriptors.MolLogP(mol))
        hbd = int(Lipinski.NumHDonors(mol))
        hba = int(Lipinski.NumHAcceptors(mol))
        rtb = int(Lipinski.NumRotatableBonds(mol))

        lid = ligand_id or f"USER_{name.upper().replace(' ', '_')}"

        return Ligand(
            ligand_id=lid,
            name=name.strip(),
            smiles=canonical_smiles,
            molecular_weight=mw,
            logp=logp,
            hbd=hbd,
            hba=hba,
            rotatable_bonds=rtb,
            source="User Literature Input"
        )
    except Exception as e:
        print(f"  ❌ Error processing SMILES with RDKit: {e}")
        return None


class HumanInterface:

    @staticmethod
    def prompt_execution_depth() -> int:
        """
        Prompt user at start of pipeline for desired execution depth.
        Returns the maximum stage index (0 to 16) to execute.
        """
        print("\n" + "=" * 70)
        print("🎯 HUMAN INTERFACE: SELECT PIPELINE EXECUTION DEPTH")
        print("=" * 70)
        print("Choose how far the pipeline should execute:")
        print("  [0] Full Pipeline (Run all 17 stages: Stage 00 to 16) [Default]")
        print("  [1] Target & Protein Mapping (Stop after Stage 04)")
        print("  [2] Structure Search & Download (Stop after Stage 06)")
        print("  [3] Binding Pocket Detection (Stop after Stage 08)")
        print("  [4] Variant Retrieval & Impact Analysis (Stop after Stage 10)")
        print("  [5] Ligand Discovery & Screening (Stop after Stage 11)")
        print("  [6] Molecular Docking & Candidate Ranking (Stop after Stage 13)")
        print("  [7] Custom: Specify exact max stage index (0–16)")
        print("=" * 70)

        depth_map = {
            "0": 16,
            "1": 4,
            "2": 6,
            "3": 8,
            "4": 10,
            "5": 11,
            "6": 13
        }

        try:
            choice = input("\nSelect option [0-7] (Press Enter for Full Pipeline [0]): ").strip()
            if not choice or choice == "0":
                print("✓ Selected: Full Pipeline Execution (Stage 00 to 16)\n")
                return 16

            if choice in depth_map:
                max_stage = depth_map[choice]
                print(f"✓ Selected: Execution up to Stage {max_stage:02d}\n")
                return max_stage

            if choice == "7":
                custom = input("Enter max stage index (0–16): ").strip()
                if custom.isdigit() and 0 <= int(custom) <= 16:
                    max_stage = int(custom)
                    print(f"✓ Selected: Execution up to Stage {max_stage:02d}\n")
                    return max_stage

            print("⚠️ Invalid choice. Defaulting to Full Pipeline (Stage 16).\n")
            return 16
        except (KeyboardInterrupt, EOFError):
            print("\n✓ Defaulting to Full Pipeline (Stage 16).\n")
            return 16

    # ------------------------------------------------------------------

    @staticmethod
    def prompt_protein_structure_override(current_structure: Structure, protein) -> Structure:
        """
        Prompt user to inspect and optionally override the target protein structure
        with a literature PDB ID or custom local .pdb file path.
        """
        print("\n" + "-" * 70)
        print("🧬 HUMAN INTERFACE: PROTEIN STRUCTURE SELECTION & OVERRIDE")
        print("-" * 70)

        curr_id = getattr(current_structure, "pdb_id", "None") or "None"
        curr_file = getattr(current_structure, "file_path", "None") or "None"
        print(f"Current Pipeline-Selected Structure:")
        print(f"  • PDB ID   : {curr_id}")
        print(f"  • File Path: {curr_file}")
        print("-" * 70)
        print("Would you like to override this structure with literature data?")
        print("  [1] Keep pipeline-selected structure [Default]")
        print("  [2] Specify a custom PDB ID from RCSB PDB (e.g. 2ARF)")
        print("  [3] Provide a local .pdb file path from your literature research")
        print("-" * 70)

        try:
            choice = input("Select option [1-3] (Press Enter to keep current): ").strip()
            if not choice or choice == "1":
                print("✓ Retaining pipeline-selected structure.\n")
                return current_structure

            if choice == "2":
                pdb_input = input("Enter custom 4-character PDB ID (e.g. 2ARF): ").strip().upper()
                if len(pdb_input) == 4 and pdb_input.isalnum():
                    new_struct = Structure(pdb_id=pdb_input)
                    print(f"✓ User override: Set target structure to PDB ID '{pdb_input}'.\n")
                    return new_struct
                else:
                    print(f"❌ Invalid PDB ID '{pdb_input}'. Keeping pipeline-selected structure.\n")
                    return current_structure

            if choice == "3":
                file_input = input("Enter absolute or relative path to local .pdb file: ").strip()
                path = Path(file_input).expanduser().resolve()
                if path.exists() and path.suffix.lower() == ".pdb":
                    new_struct = Structure(pdb_id=f"CUSTOM_{path.stem}", file_path=str(path))
                    print(f"✓ User override: Set target structure to local file '{path}'.\n")
                    return new_struct
                else:
                    print(f"❌ File not found or not a .pdb file: '{file_input}'. Keeping pipeline-selected structure.\n")
                    return current_structure

        except (KeyboardInterrupt, EOFError):
            print("\n✓ Retaining pipeline-selected structure.\n")
            return current_structure

        return current_structure

    # ------------------------------------------------------------------

    @staticmethod
    def prompt_ligand_override(screened_ligands: List[Ligand]) -> List[Ligand]:
        """
        Prompt user to inspect screened ligands and optionally add or substitute
        custom literature candidate ligands (SMILES / ChEMBL / PubChem).
        """
        print("\n" + "-" * 70)
        print("🧪 HUMAN INTERFACE: LIGAND SELECTION & LITERATURE OVERRIDE")
        print("-" * 70)
        print(f"Pipeline prepared {len(screened_ligands)} candidate ligand(s) for docking.")
        if screened_ligands:
            sample_names = ", ".join(l.name for l in screened_ligands[:5])
            print(f"Sample ligands: {sample_names}...")
        print("-" * 70)
        print("Would you like to include custom literature candidate ligands?")
        print("  [1] Proceed with pipeline-discovered ligands [Default]")
        print("  [2] Add custom literature ligand(s) to the screening set")
        print("  [3] Replace all ligands with custom literature ligand(s)")
        print("-" * 70)

        try:
            choice = input("Select option [1-3] (Press Enter to proceed): ").strip()
            if not choice or choice == "1":
                print("✓ Proceeding with pipeline-discovered ligands.\n")
                return screened_ligands

            is_replace = (choice == "3")
            custom_ligands: List[Ligand] = [] if is_replace else list(screened_ligands)

            print("\n--- Enter Custom Literature Ligands ---")
            print("Type 'done' or press Enter when finished adding ligands.\n")

            added_count = 0
            while True:
                name_input = input(f"Custom Ligand #{added_count + 1} Name (or 'done'): ").strip()
                if not name_input or name_input.lower() == "done":
                    break

                smiles_input = input(f"Enter SMILES for '{name_input}': ").strip()
                if not smiles_input:
                    print("  ⚠️ SMILES cannot be empty. Skipping.")
                    continue

                lig = helper_parse_smiles_to_ligand(name=name_input, smiles=smiles_input)
                if lig:
                    custom_ligands.append(lig)
                    added_count += 1
                    print(f"  ✓ Added '{lig.name}' (MW={lig.molecular_weight:.1f}, LogP={lig.logp:.2f})")

            if is_replace and not custom_ligands:
                print("⚠️ No valid custom ligands entered. Falling back to pipeline-discovered set.\n")
                return screened_ligands

            print(f"\n✓ Final screening set contains {len(custom_ligands)} ligand(s) ({added_count} custom added).\n")
            return custom_ligands

        except (KeyboardInterrupt, EOFError):
            print("\n✓ Proceeding with current ligand set.\n")
            return screened_ligands
