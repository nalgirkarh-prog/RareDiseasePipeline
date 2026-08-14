import os
import subprocess


class LigandPreparer:

    def prepare(self, ligand):

        os.makedirs("output/ligands", exist_ok=True)

        smi = f"output/ligands/{ligand.ligand_id}.smi"

        smiles = ligand.smiles
        if "." in smiles:
            smiles = max(smiles.split("."), key=len)

        with open(smi, "w") as f:

            f.write(smiles)

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
