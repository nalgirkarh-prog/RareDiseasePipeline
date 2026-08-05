from clients.ensembl import EnsemblClient
from models.protein import Protein


class ProteinFetcher:

    def __init__(self):

        self.client = EnsemblClient()



    def run(self, transcript):

        print("▶ Fetching protein")


        protein = self.fetch(transcript)


        if protein is None:

            raise ValueError(
                "Protein sequence not found"
            )


        print(
            f"✓ Protein fetched: {protein.protein_id}"
        )


        return protein




    def fetch(self, transcript):

        if transcript is None:

            return None



        protein_id = transcript.protein_id


        if protein_id is None:

            return None



        data = self.client.fetch_protein_sequence(
            protein_id
        )


        sequence = data.get("seq")


        protein = Protein(

            protein_id=protein_id,

            sequence=sequence,

            length=len(sequence) if sequence else None

        )


        return protein
