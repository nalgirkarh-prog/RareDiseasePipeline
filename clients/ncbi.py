import requests


class NCBIClient:

    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def search_gene(self, disease):

        url = (
            self.BASE +
            "esearch.fcgi"
        )

        params = {

            "db": "gene",

            "term": disease,

            "retmode": "json"

        }

        r = requests.get(url, params=params)

        data = r.json()

        ids = data["esearchresult"]["idlist"]

        if len(ids) == 0:

            return {

                "Status": "Disease Not Found"

            }

        gene_id = ids[0]

        return self.fetch_gene(gene_id)

    def fetch_gene(self, gene_id):

        url = (

            self.BASE +

            "esummary.fcgi"

        )

        params = {

            "db": "gene",

            "id": gene_id,

            "retmode": "json"

        }

        r = requests.get(url, params=params)

        data = r.json()

        result = data["result"][gene_id]

        return {

            "Gene ID": result.get("uid"),

            "Name": result.get("name"),

            "Description": result.get("description"),

            "Organism": result["organism"]["scientificname"],

            "Chromosome": result.get("chromosome"),

            "Map Location": result.get("maplocation")

        }
