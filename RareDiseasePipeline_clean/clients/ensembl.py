import requests
import time


BASE_URL = "https://rest.ensembl.org"



class EnsemblClient:


    def __init__(self):

        self.headers = {

            "Content-Type": "application/json"

        }



    def _get(self, url, params=None):


        attempts = 3


        for attempt in range(1, attempts + 1):


            try:


                response = requests.get(

                    url,

                    headers=self.headers,

                    params=params,

                    timeout=90

                )


                response.raise_for_status()


                return response.json()



            except requests.exceptions.RequestException as e:


                print(
                    f"⚠ Ensembl request failed "
                    f"(attempt {attempt}/{attempts})"
                )


                if attempt < attempts:

                    time.sleep(
                        attempt * 5
                    )


                else:

                    raise e





    def fetch_gene(self, symbol):


        url = (
            f"{BASE_URL}/lookup/symbol/"
            f"homo_sapiens/{symbol}"
        )


        params = {

            "expand": 1

        }


        return self._get(

            url,

            params

        )





    def fetch_transcripts(self, symbol):


        data = self.fetch_gene(
            symbol
        )


        return data.get(

            "Transcript",

            []

        )





    def fetch_canonical_transcript(self, symbol):


        transcripts = self.fetch_transcripts(
            symbol
        )


        for transcript in transcripts:


            if transcript.get(
                "is_canonical",
                0
            ) == 1:


                return transcript



        return None





    def fetch_protein_sequence(self, protein_id):


        url = (
            f"{BASE_URL}/sequence/id/"
            f"{protein_id}"
        )


        return self._get(
            url
        )
