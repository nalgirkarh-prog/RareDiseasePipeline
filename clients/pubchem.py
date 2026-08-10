import requests


class PubChemClient:


    BASE = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    )


    def search_compounds(
        self,
        query
    ):


        url = (
            f"{self.BASE}/compound/name/"
            f"{query}/cids/JSON"
        )


        response = requests.get(
            url
        )


        response.raise_for_status()


        return response.json()



    def get_properties(
        self,
        cid
    ):


        url = (
            f"{self.BASE}/compound/cid/"
            f"{cid}/property/"
            "MolecularWeight,"
            "XLogP,"
            "HBondDonorCount,"
            "HBondAcceptorCount,"
            "RotatableBondCount,"
            "CanonicalSMILES/"
            "JSON"
        )


        response = requests.get(
            url
        )


        response.raise_for_status()


        return response.json()
