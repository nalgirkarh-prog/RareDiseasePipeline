import os
import requests


class StructureDownloader:

    def download_pdb(self, pdb_id):

        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"

        folder = "database/structures"

        os.makedirs(folder, exist_ok=True)

        outfile = os.path.join(folder, f"{pdb_id}.pdb")

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            return None

        with open(outfile, "w") as f:
            f.write(response.text)

        return outfile


    def download_alphafold(self, uniprot):

        url = (
            "https://alphafold.ebi.ac.uk/files/"
            f"AF-{uniprot}-F1-model_v4.pdb"
        )

        folder = "database/structures"

        os.makedirs(folder, exist_ok=True)

        outfile = os.path.join(folder, f"AF_{uniprot}.pdb")

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            return None

        with open(outfile, "w") as f:
            f.write(response.text)

        return outfile
