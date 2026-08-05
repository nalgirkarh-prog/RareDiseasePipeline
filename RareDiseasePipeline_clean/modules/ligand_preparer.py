import os
import subprocess


class LigandPreparer:

    def prepare(self, ligand):

        os.makedirs("output/ligands", exist_ok=True)

        smi = f"output/ligands/{ligand.ligand_id}.smi"

        with open(smi, "w") as f:

            f.write(ligand.smiles)

        pdbqt = f"output/ligands/{ligand.ligand_id}.pdbqt"

        subprocess.run(

            [

                "obabel",

                smi,

                "-O",

                pdbqt,

                "--gen3d"

            ],

            check=True

        )

        return pdbqt
