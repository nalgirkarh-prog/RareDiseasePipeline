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
        folder = "database/structures"
        os.makedirs(folder, exist_ok=True)
        outfile = os.path.join(folder, f"AF_{uniprot}.pdb")

        # 1. Dynamic lookup via AlphaFold EBI prediction API
        try:
            api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot}"
            r = requests.get(api_url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    pdb_url = data[0].get("pdbUrl")
                    if pdb_url:
                        resp = requests.get(pdb_url, timeout=60)
                        if resp.status_code == 200 and len(resp.text) > 500:
                            with open(outfile, "w") as f:
                                f.write(resp.text)
                            return outfile
        except Exception:
            pass

        # 2. Fallback to direct model versions (v6, v5, v4)
        for ver in ["v6", "v5", "v4"]:
            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot}-F1-model_{ver}.pdb"
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200 and len(resp.text) > 500:
                    with open(outfile, "w") as f:
                        f.write(resp.text)
                    return outfile
            except Exception:
                continue

        return None
