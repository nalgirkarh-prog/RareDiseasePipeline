from clients.uniprot import UniProtClient


class UniProtFetcher:

    def __init__(self):

        self.client = UniProtClient()



    def run(self, protein):

        print("▶ Mapping UniProt")


        protein = self.fetch(protein)


        if protein.uniprot:

            print(
                f"✓ UniProt mapped: {protein.uniprot}"
            )

        else:

            print(
                "⚠ UniProt mapping not found"
            )


        return protein




    def fetch(self, protein):

        data = self.client.fetch_from_ensembl(
            protein.protein_id
        )


        results = data.get(
            "results",
            []
        )


        if len(results) == 0:

            return protein



        entry = results[0]


        protein.uniprot = entry[
            "primaryAccession"
        ]


        return protein
