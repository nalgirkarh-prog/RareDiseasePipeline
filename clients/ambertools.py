import subprocess
from pathlib import Path


class AmberToolsClient:

    def export_ligand(self, ligand, outdir):

        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        smiles_file = outdir / "ligand.smi"
        mol2_file = outdir / "ligand.mol2"

        # Write SMILES
        with open(smiles_file, "w") as f:
            f.write(f"{ligand.smiles} {ligand.name}\n")


        # Convert SMILES -> MOL2 with 3D coordinates
        subprocess.run(
            [
                "obabel",
                "-ismi",
                str(smiles_file),
                "-omol2",
                "-O",
                str(mol2_file),
                "--gen3d",
                "--title",
                "LIG"
            ],
            check=True
        )


        print("✓ Ligand MOL2 generated")

        return mol2_file



    def parameterize(self, outdir):

        outdir = Path(outdir)

        mol2 = outdir / "ligand.mol2"

        gaff_mol2 = outdir / "ligand_gaff.mol2"

        frcmod = outdir / "ligand.frcmod"


        print("Generating AMBER ligand parameters...")


        # Generate GAFF atom types + AM1-BCC charges
        subprocess.run(
            [
                "antechamber",
                "-i",
                str(mol2),
                "-fi",
                "mol2",
                "-o",
                str(gaff_mol2),
                "-fo",
                "mol2",
                "-c",
                "bcc",
                "-at",
                "gaff2",
                "-nc",
                "0",
                "-s",
                "2"
            ],
            check=True
        )


        # Generate missing force-field parameters
        subprocess.run(
            [
                "parmchk2",
                "-i",
                str(gaff_mol2),
                "-f",
                "mol2",
                "-o",
                str(frcmod)
            ],
            check=True
        )


        print("✓ Ligand parameters generated")


        return {
            "mol2": gaff_mol2,
            "frcmod": frcmod
        }
