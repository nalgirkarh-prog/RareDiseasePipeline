import csv
import json
from pathlib import Path

from modules.medicinal_filters import MedicinalFilters


class DrugEvaluator:

    def __init__(self):

        self.filters = MedicinalFilters()


    def evaluate(self, ranked_candidates):

        print("▶ Evaluating drug candidates")

        evaluated = []

        for candidate in ranked_candidates:

            ligand = candidate["ligand"]

            report = self.filters.evaluate(
                ligand.smiles
            )

            if report is None:
                continue


            candidate["evaluation"] = report

            candidate["drug_score"] = self.calculate_score(
                candidate,
                report
            )


            print("\n--------------------------------------")
            print(f"Ligand      : {ligand.name}")
            print(f"Affinity    : {candidate['affinity']:.2f} kcal/mol")
            print(f"H-Bond      : {report.get('hbond', False)}")
            print(f"Lipinski    : {report['lipinski']}")
            print(f"Veber       : {report['veber']}")
            print(f"Ghose       : {report['ghose']}")
            print(f"Egan        : {report['egan']}")
            print(f"Muegge      : {report['muegge']}")
            print(f"QED         : {report['qed']:.3f}")
            print(f"Drug Score  : {candidate['drug_score']}")


            evaluated.append(candidate)



        evaluated.sort(
            key=lambda x: x["drug_score"],
            reverse=True
        )


        for rank, candidate in enumerate(
            evaluated,
            start=1
        ):

            candidate["drug_rank"] = rank



        self.save_csv(evaluated)

        self.save_json(evaluated)


        return evaluated



    def calculate_score(self, candidate, report):

        score = 0


        if report.get("hbond"):
            score += 10


        if report["lipinski"]:
            score += 20


        if report["veber"]:
            score += 15


        if report["ghose"]:
            score += 10


        if report["egan"]:
            score += 10


        if report["muegge"]:
            score += 15



        score += report["qed"] * 30



        affinity = candidate.get("affinity")

        # Award affinity points ONLY for negative binding affinity (< 0 kcal/mol)
        if affinity is not None and affinity < 0:
            score += min((-affinity) * 3, 30)


        return round(score, 2)



    def save_csv(self, evaluated):

        Path("output").mkdir(
            exist_ok=True
        )


        with open(
            "output/drug_evaluation.csv",
            "w",
            newline=""
        ) as f:


            writer = csv.writer(f)


            writer.writerow([
                "Rank",
                "Ligand",
                "Affinity",
                "Drug Score",
                "QED",
                "HBond",
                "Lipinski",
                "Veber",
                "Ghose",
                "Egan",
                "Muegge"
            ])



            for c in evaluated:

                r = c["evaluation"]


                writer.writerow([

                    c["drug_rank"],

                    c["ligand"].name,

                    c["affinity"],

                    c["drug_score"],

                    round(r["qed"], 3),

                    r.get("hbond", False),

                    r["lipinski"],

                    r["veber"],

                    r["ghose"],

                    r["egan"],

                    r["muegge"]

                ])





    def save_json(self, evaluated):

        output = []


        for c in evaluated:

            r = c["evaluation"]


            output.append({

                "rank": c["drug_rank"],

                "ligand": c["ligand"].name,

                "affinity": c["affinity"],

                "drug_score": c["drug_score"],

                "evaluation": r

            })



        with open(
            "output/drug_evaluation.json",
            "w"
        ) as f:


            json.dump(
                output,
                f,
                indent=4
            )
