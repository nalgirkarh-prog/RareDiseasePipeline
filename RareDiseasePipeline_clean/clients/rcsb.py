import requests


class RCSBClient:

    SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"

    def search(self, uniprot):

        query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute":
                    "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                    "operator": "exact_match",
                    "value": uniprot
                }
            },
            "return_type": "entry"
        }

        response = requests.post(
            self.SEARCH_URL,
            json=query,
            timeout=30
        )

        response.raise_for_status()

        return response.json()
