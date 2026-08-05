from modules.report_generator import ReportGenerator


class ReportStage:

    def __init__(self):

        pass


    def run(self, context):

        print("\nGenerating research report...")

        generator = ReportGenerator(
            context
        )

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
            print("🏆 FINAL PIPELINE RESULTS 🏆")
            print("==============================================")
            print(f"Top Candidate : {ligand_name}")
            print(f"Binding Affinity : {affinity} kcal/mol")
            print(f"Overall Drug Score : {score}")
            print("==============================================\n")

        return report
