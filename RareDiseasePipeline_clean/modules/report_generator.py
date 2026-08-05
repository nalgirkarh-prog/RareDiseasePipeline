"""
RareDiseasePipeline
Report Generator

Creates structured research reports from pipeline context.

Future extensions:
- Markdown report generation
- PDF report generation
- LLM-assisted hypothesis generation
"""

import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:


    def __init__(self, context):

        self.context = context


    # =====================================================
    # Disease formatting helper
    # =====================================================

    def get_disease_name(self):

        disease = self.context.get(
            "disease"
        )

        if hasattr(disease, "name"):

            return disease.name

        return str(disease)


    # =====================================================
    # Build structured report
    # =====================================================

    def build_report(self):

        report = {


            "metadata": {

                "generated": str(
                    datetime.now()
                ),

                "pipeline":
                    "RareDiseasePipeline v2"

            },


            "disease": {

                "name":
                    self.get_disease_name()

            },


            "gene":
                self.context.get(
                    "gene"
                ),


            "gene_information":
                self.context.get(
                    "gene_info"
                ),


            "transcript":
                self.context.get(
                    "transcript"
                ),


            "protein":
                self.context.get(
                    "protein"
                ),


            "structure": {

                "data":
                    self.context.get(
                        "structure"
                    ),

                "file":
                    self.context.get(
                        "pdb_file"
                    )

            },


            "regulation":
                self.context.get(
                    "regulation"
                ),


            "binding_pockets":
                self.context.get(
                    "pockets"
                ),


            "variants": {

                "raw":
                    self.context.get(
                        "variants"
                    ),

                "analysis":
                    self.context.get(
                        "variant_analysis"
                    )

            },


            "drug_discovery": {

                "ligands":
                    self.context.get(
                        "ligands"
                    ),


                "docking_results":
                    self.context.get(
                        "docking_results"
                    ),


                "ranking":
                    self.context.get(
                        "ranked_candidates"
                    ),


                "evaluation":
                    self.context.get(
                        "evaluated_candidates"
                    )

            },


            "simulation":

                self.context.get(
                    "simulation"
                )


        }


        return report



    # =====================================================
    # Save JSON report
    # =====================================================

    def save_json(self, path):

        report = self.build_report()


        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            path,
            "w"
        ) as file:


            json.dump(

                report,

                file,

                indent=4,

                default=str

            )


        return path



    # =====================================================
    # Pipeline entry point
    # =====================================================

    def generate(self):

        """
        Main interface used by Stage 16.
        """

        output_path = (
            "output/reports/research_report.json"
        )


        self.save_json(
            output_path
        )


        return self.build_report()
