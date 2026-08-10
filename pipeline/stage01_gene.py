from clients.ensembl import EnsemblClient
from models.gene import Gene


class GeneFetcher:

    def __init__(self):

        self.client = EnsemblClient()



    def run(self, data):

        print("▶ Fetching gene")


        if isinstance(data, dict):

            symbol = data["gene"]

        else:

            symbol = data


        gene = self.fetch(symbol)


        print(f"✓ Gene fetched: {gene.symbol}")


        return gene




    def fetch(self, symbol):

        data = self.client.fetch_gene(symbol)


        transcripts = []


        for transcript in data.get("Transcript", []):

            transcripts.append(
                transcript["id"]
            )



        gene = Gene(

            symbol=symbol,

            gene_name=data.get("display_name"),

            ensembl_id=data.get("id"),

            chromosome=data.get("seq_region_name"),

            start=data.get("start"),

            end=data.get("end"),

            strand=data.get("strand"),

            description=data.get("description"),

            transcripts=transcripts

        )


        return gene
