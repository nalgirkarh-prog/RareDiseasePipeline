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


def serialize_object(obj):
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, list):
        return [serialize_object(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    return obj


class ReportGenerator:

    def __init__(self, context):
        self.context = context

    # =====================================================
    # Disease formatting helper
    # =====================================================

    def get_disease_name(self):
        disease = self.context.get("disease")
        if hasattr(disease, "name"):
            return disease.name
        return str(disease)

    def get_docking_winner(self):
        ranked = self.context.get("ranked_candidates", [])
        if ranked:
            top = ranked[0]
            lig = top.get("ligand")
            lig_name = getattr(lig, "name", None) or top.get("ligand_name") or str(lig)
            return {
                "ligand": lig_name,
                "docking_score_kcal_per_mol": top.get("affinity"),
                "status": top.get("status", "success")
            }
        return None

    def get_drug_prioritization_winner(self):
        evaluated = self.context.get("evaluated_candidates", [])
        if evaluated:
            top = evaluated[0]
            lig = top.get("ligand")
            lig_name = getattr(lig, "name", None) or top.get("ligand_name") or str(lig)
            return {
                "ligand": lig_name,
                "docking_score_kcal_per_mol": top.get("affinity"),
                "drug_score": top.get("drug_score"),
                "qed": top.get("evaluation", {}).get("qed"),
                "drug_rank": top.get("drug_rank", 1)
            }
        return None

    # =====================================================
    # Build structured report
    # =====================================================

    def build_report(self):
        report = {
            "metadata": {
                "generated": str(datetime.now()),
                "pipeline": "RareDiseasePipeline v2"
            },
            "disease": {
                "name": self.get_disease_name()
            },
            "gene": self.context.get("gene"),
            "gene_information": self.context.get("gene_info"),
            "transcript": self.context.get("transcript"),
            "protein": self.context.get("protein"),
            "structure": {
                "data": self.context.get("structure"),
                "file": self.context.get("pdb_file")
            },
            "regulation": self.context.get("regulation"),
            "binding_pockets": self.context.get("pockets"),
            "variants": {
                "raw": self.context.get("variants"),
                "analysis": self.context.get("variant_analysis")
            },
            "drug_discovery": {
                "ligands": self.context.get("ligands"),
                "docking_results": self.context.get("docking_results"),
                "ranking": self.context.get("ranked_candidates"),
                "evaluation": self.context.get("evaluated_candidates"),
                "docking_winner": self.get_docking_winner(),
                "drug_prioritization_winner": self.get_drug_prioritization_winner()
            },
            "simulation": self.context.get("simulation"),
            "structure_preparation": self.context.get("structure_preparation", {})
        }
        return report

    # =====================================================
    # Save JSON report
    # =====================================================

    def save_json(self, path):
        report = self.build_report()
        serialized = serialize_object(report)

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(path, "w") as file:
            json.dump(
                serialized,
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
        output_path = "output/reports/research_report.json"
        self.save_json(output_path)
        return self.build_report()
