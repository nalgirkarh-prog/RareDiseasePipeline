import os
import subprocess
import requests


class LigandPreparation:

    def prepare(
        self,
        ligand
    ):

        sdf = (
            f"cache/{ligand.ligand_id}.sdf"
        )

        pdbqt = (
            f"cache/{ligand.ligand_id}.pdbqt"
        )

        os.makedirs(
            "cache",
            exist_ok=True
        )

        if not os.path.exists(sdf):

            url = (
                "https://www.ebi.ac.uk/chembl/api/data/"
                f"molecule/{ligand.ligand_id}.sdf"
            )

            r = requests.get(url)

            if r.status_code != 200:
                return None

            with open(sdf, "wb") as f:
                f.write(r.content)

        if not os.path.exists(pdbqt):

            subprocess.run(

                [
                    "obabel",
                    sdf,
                    "-O",
                    pdbqt,
                    "--gen3d"
                ],

                check=True

            )

        return pdbqt
