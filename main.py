#!/usr/bin/env python3

"""
RareDiseasePipeline

Automated Genomic Drug Discovery Pipeline

Workflow:

Disease
 ↓
Gene Identification
 ↓
Transcript Discovery
 ↓
Protein Extraction
 ↓
UniProt Mapping
 ↓
Structure Identification
 ↓
Structure Download
 ↓
Regulatory Analysis
 ↓
Binding Pocket Detection
"""


import os
import sys


# Ensure project root and python bin directory are in PATH and sys.path
bin_dir = os.path.dirname(sys.executable)
if bin_dir and bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Pipeline engine
from pipeline.pipeline import Pipeline


# Models
from models.disease import Disease


# Pipeline stages

from pipeline.stage00_resolve import DiseaseResolver
from pipeline.stage01_gene import GeneFetcher
from pipeline.stage02_transcript import TranscriptFetcher
from pipeline.stage03_protein import ProteinFetcher
from pipeline.stage04_uniprot import UniProtFetcher
from pipeline.stage05_structure import StructureFetcher
from pipeline.stage06_download import DownloadStage
from pipeline.stage07_regulation import RegulationFetcher
from pipeline.stage08_pocket import PocketDetector
from pipeline.stage09_variants import VariantFetcher
from pipeline.stage10_variant_analysis import VariantAnalysisStage
from pipeline.stage11_ligand import LigandScreeningStage
from pipeline.stage12_docking import DockingStage
from pipeline.stage13_ranking import DockingRankingStage
from pipeline.stage14_drug_evaluation import DrugEvaluationStage
from pipeline.stage15_solution_builder import SolutionBuilderStage
from pipeline.stage16_report import ReportStage

def banner():

    print("""
=================================================

        🧬 RareDiseasePipeline

        Automated Genomic Drug Discovery Pipeline

=================================================
""")

def main():

    banner()

    disease_name = input(
        "Enter disease name: "
    )


    print(
        f"\n🧬 Initializing project for: {disease_name}\n"
    )


    # Create disease object

    project = Disease(
        name=disease_name
    )


    # Create pipeline

    pipeline = Pipeline()


    # Register stages

    pipeline.add_stage(
        DiseaseResolver()
    )

    pipeline.add_stage(
        GeneFetcher()
    )

    pipeline.add_stage(
        TranscriptFetcher()
    )

    pipeline.add_stage(
        ProteinFetcher()
    )

    pipeline.add_stage(
        UniProtFetcher()
    )

    pipeline.add_stage(
        StructureFetcher()
    )

    pipeline.add_stage(
        DownloadStage()
    )

    pipeline.add_stage(
        RegulationFetcher()
    )

    pipeline.add_stage(
        PocketDetector()
    )
    pipeline.add_stage(
    VariantFetcher()
    )
    pipeline.add_stage(
    VariantAnalysisStage()
    )
    pipeline.add_stage(
    LigandScreeningStage()
    )
    pipeline.add_stage(
    DockingStage()
    )
    pipeline.add_stage(
    DockingRankingStage()
    )
    pipeline.add_stage(
    DrugEvaluationStage()
    )
    pipeline.add_stage(
    SolutionBuilderStage()
    )
    pipeline.add_stage(
    ReportStage()
    )


    print(
        "\n🚀 Starting pipeline...\n"
         )


    try:

        result = pipeline.run(
            project,
            interactive=True
        )


    except Exception as e:

        print(
            "\n❌ Pipeline execution failed"
        )

        print(
            type(e).__name__,
            ":",
            e
        )

        return


    print(
        "\n================================"
    )

    print(
        " 🧬 PIPELINE COMPLETED"
    )

    print(
        "================================\n"
    )


    print(result)

if __name__ == "__main__":

    main()
