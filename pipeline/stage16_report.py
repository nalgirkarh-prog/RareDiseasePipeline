from modules.report_generator import ReportGenerator


class ReportStage:

    def __init__(self):
        pass

    def run(self, context):

        print("\nGenerating research report...")

        generator = ReportGenerator(context)
        report = generator.generate()

        print(
            "✓ Report generated at output/reports/research_report.json"
        )

        evaluated = context.get("evaluated_candidates", [])

        if evaluated:
            top_candidate = evaluated[0]

            ligand = top_candidate.get("ligand")
            ligand_name = ligand.name if ligand else "Unknown"

            score = top_candidate.get("drug_score", "N/A")
            affinity = top_candidate.get("affinity", "N/A")

            print("\n==============================================")
            print("   COMPUTATIONAL PRIORITIZATION RESULTS")
            print("==============================================")
            print(f"Prioritized Candidate : {ligand_name}")
            print(f"Docking Score         : {affinity} kcal/mol")
            print(f"Prioritization Score  : {score}")
            print("----------------------------------------------")
            print(
                "Status: Candidate prioritized for downstream "
                "molecular-dynamics evaluation."
            )
            print(
                "Note: Computational prioritization does not establish "
                "binding affinity, biological activity, or therapeutic efficacy."
            )
            print("==============================================\n")

        return report
