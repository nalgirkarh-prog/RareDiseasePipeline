from clients.clinvar import ClinVarClient
from models.variant import Variant
import re


class VariantFetcher:

    def __init__(self):

        self.client = ClinVarClient()



    def run(self, gene):

        print("▶ Fetching variants")


        variants = self.fetch(
            gene
        )


        print(
            f"✓ Retrieved {len(variants)} variants"
        )


        return variants




    def extract_residue(self, hgvs_p):

        if not hgvs_p:

            return None


        match = re.search(
            r"(\d+)",
            hgvs_p
        )


        if match:

            return int(
                match.group(1)
            )


        return None




    def fetch(self, gene):

        print(
            "\nFetching ClinVar variants..."
        )


        variants = []


        if hasattr(gene, "symbol"):

            symbol = gene.symbol

        else:

            symbol = gene



        results = self.client.search_gene(
            symbol
        )



        ids = (
            results
            .get(
                "esearchresult",
                {}
            )
            .get(
                "idlist",
                []
            )
        )



        print(
            f"Found {len(ids)} ClinVar records"
        )



        for uid in ids[:5]:


            record = self.client.fetch_variant(
                uid
            )


            # Temporary parser
            # Full XML parser will replace this


            variants.append(

                Variant(

                    variant_id=uid,

                    gene=symbol,

                    accession=uid,

                    hgvs_c=None,

                    hgvs_p=None,

                    clinical_significance="unknown",

                    residue=None

                )

            )


        return variants
