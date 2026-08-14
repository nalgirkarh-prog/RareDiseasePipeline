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
                    timeout=30
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                # Do not retry on client errors (4xx), e.g. 400 Bad Request or 404 Not Found
                if e.response is not None and 400 <= e.response.status_code < 500:
                    return None
                if attempt < attempts:
                    time.sleep(attempt * 2)
                else:
                    return None

            except requests.exceptions.RequestException as e:
                if attempt < attempts:
                    time.sleep(attempt * 2)
                else:
                    return None

    def fetch_gene(self, symbol):
        url = (
            f"{BASE_URL}/lookup/symbol/"
            f"homo_sapiens/{symbol}"
        )
        params = {
            "expand": 1
        }
        return self._get(url, params)

    def fetch_transcripts(self, symbol):
        data = self.fetch_gene(symbol)
        if not data or not isinstance(data, dict):
            return []
        return data.get("Transcript", [])

    def fetch_canonical_transcript(self, symbol):
        transcripts = self.fetch_transcripts(symbol)
        for transcript in transcripts:
            if transcript.get("is_canonical", 0) == 1:
                return transcript
        return None

    def fetch_protein_sequence(self, protein_id):
        url = (
            f"{BASE_URL}/sequence/id/"
            f"{protein_id}"
        )
        return self._get(url)

    # ------------------------------------------------------------------

    def vep_hgvs(self, hgvs_c: str, transcript_id: str | None = None):
        """
        Call the Ensembl VEP REST endpoint for a coding HGVS notation
        (e.g. "NM_004992.4:c.397C>T" or "ENST00000303391:c.397C>T").
        Returns the most severe consequence term, or None if unavailable.
        """
        if not hgvs_c:
            return None

        import urllib.parse

        candidates = []
        if ":" in hgvs_c:
            candidates.append(hgvs_c)
        else:
            if transcript_id:
                candidates.append(f"{transcript_id}:{hgvs_c}")
            candidates.append(hgvs_c)

        for candidate in candidates:
            encoded = urllib.parse.quote(candidate, safe="")
            url = f"{BASE_URL}/vep/human/hgvs/{encoded}"
            data = self._get(url)
            if data and isinstance(data, list) and len(data) > 0:
                top = data[0]
                consequence = top.get("most_severe_consequence")
                if consequence:
                    return consequence

        return None
