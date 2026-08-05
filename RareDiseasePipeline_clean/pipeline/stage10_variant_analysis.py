from modules.variant_analysis import VariantAnalyzer


class VariantAnalysisStage:


    def __init__(self):

        self.analyzer = VariantAnalyzer()



    def run(
        self,
        variants,
        protein
    ):


        print(
            "\nAnalyzing variants..."
        )


        analyzed = []


        for variant in variants:


            result = {

    "variant_id":
        variant.variant_id,

    "gene":
        variant.gene,

    "accession":
        variant.accession,

    "hgvs_c":
        variant.hgvs_c,

    "hgvs_p":
        variant.hgvs_p,

    "residue":
        variant.residue,

    "clinical_significance":
        variant.clinical_significance,

    "consequence":
        variant.consequence,

    "mapped":
        self.analyzer.map_to_sequence(
            variant.residue,
            protein.sequence
        ),

    "region":
        self.analyzer.predict_region(
            variant.residue
        )


            }


            analyzed.append(
                result
            )


        print(
            f"Analyzed {len(analyzed)} variants"
        )


        return analyzed
