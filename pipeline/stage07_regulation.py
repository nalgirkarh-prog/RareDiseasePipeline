from clients.stringdb import STRINGClient
from models.interaction import Interaction


class RegulationFetcher:

    def __init__(self):

        self.client = STRINGClient()



    def run(self, gene):

        print("▶ Fetching regulatory interactions")


        interactions = self.fetch(gene)


        print(
            f"✓ Retrieved {len(interactions)} interactions"
        )


        return interactions




    def fetch(self, gene):

        if hasattr(gene, "symbol"):

            symbol = gene.symbol

        else:

            symbol = gene


        raw = self.client.fetch_interactions(
            symbol
        )


        interactions = []


        for item in raw:

            interaction = Interaction(

                protein=item.get(
                    "preferredName_B"
                ),

                score=item.get(
                    "score",
                    0.0
                )

            )


            interactions.append(
                interaction
            )


        return interactions
