from pathlib import Path
import csv
import json


class DockingRankingStage:


    def run(self, context):

        print("▶ Ranking docked ligands")


        docking_results = context.get(
            "docking_results",
            []
        )


        ranked = []


        for result in docking_results:


            ranked.append(

                {

                    "ligand": result["ligand"],

                    "affinity": result["affinity"]

                }

            )



        ranked.sort(

            key=lambda x: x["affinity"]

        )



        self.save_csv(
            ranked
        )


        self.save_json(
            ranked
        )


        context["ranked_candidates"] = ranked


        print(
            f"✓ Ranked {len(ranked)} ligands"
        )


        return ranked





    def save_csv(self, results):

        Path(
            "output"
        ).mkdir(
            exist_ok=True
        )


        with open(

            "output/docking_ranking.csv",

            "w",

            newline=""

        ) as f:


            writer = csv.writer(f)


            writer.writerow(

                [
                    "Ligand",
                    "Affinity"
                ]

            )


            for item in results:

                writer.writerow(

                    [
                        item["ligand"].name,

                        item["affinity"]

                    ]

                )





    def save_json(self, results):

        output = []


        for item in results:


            output.append(

                {

                    "ligand":
                        item["ligand"].name,

                    "affinity":
                        item["affinity"]

                }

            )



        with open(

            "output/docking_ranking.json",

            "w"

        ) as f:


            json.dump(

                output,

                f,

                indent=4

            )
