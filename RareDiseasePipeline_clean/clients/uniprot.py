import requests


class UniProtClient:

    BASE_URL = "https://rest.uniprot.org"


    def fetch_from_ensembl(self, ensp):

        url = (
            f"{self.BASE_URL}/uniprotkb/search"
            f"?query=xref:Ensembl-{ensp}&format=json"
        )

        response = requests.get(url, timeout=30)

        response.raise_for_status()

        return response.json()
