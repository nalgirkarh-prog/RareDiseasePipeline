import requests


class STRINGClient:

    BASE_URL = "https://string-db.org/api/json"

    def fetch_interactions(self, gene):

        url = f"{self.BASE_URL}/network"

        params = {
            "identifiers": gene,
            "species": 9606
        }

        response = requests.get(url, params=params, timeout=30)

        response.raise_for_status()

        return response.json()
