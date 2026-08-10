from clients.rcsb import RCSBClient
from models.structure import Structure


class StructureFetcher:

    def __init__(self):

        self.client = RCSBClient()



    def run(self, protein):

        print("▶ Fetching structure")


        structure = self.fetch(protein)


        if structure is None:

            print("⚠ No PDB structure found, falling back to AlphaFold")
            
            structure = Structure()

        else:
            print(
                f"✓ Structure found: {structure.pdb_id}"
            )


        return structure




    def fetch(self, protein):

        if protein.uniprot is None:

            return None



        data = self.client.search(
            protein.uniprot
        )


        hits = data.get(
            "result_set",
            []
        )


        if len(hits) == 0:

            return None



        pdb = hits[0]["identifier"]


        structure = Structure(

            pdb_id=pdb

        )


        return structure
