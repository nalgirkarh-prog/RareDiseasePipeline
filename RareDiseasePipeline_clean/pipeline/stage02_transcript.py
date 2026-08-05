from clients.ensembl import EnsemblClient
from models.transcript import Transcript


class TranscriptFetcher:

    def __init__(self):

        self.client = EnsemblClient()



    def run(self, gene):

        print("▶ Fetching transcript")


        if hasattr(gene, "symbol"):

            symbol = gene.symbol

        else:

            symbol = gene


        transcript = self.fetch(symbol)


        if transcript is None:

            raise ValueError(
                f"Transcript not found for {symbol}"
            )


        print(
            f"✓ Transcript fetched: {transcript.transcript_id}"
        )


        return transcript




    def fetch(self, symbol):

        data = self.client.fetch_canonical_transcript(symbol)


        if data is None:

            return None



        transcript = Transcript(

            transcript_id=data["id"],

            transcript_name=data.get("display_name"),

            canonical=True,

            biotype=data.get("biotype"),

            protein_id=data.get("Translation", {}).get("id")

        )


        return transcript
