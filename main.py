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
import shutil
import subprocess


# Auto-detect and switch to 'rdpipeline' Conda environment if running under system/mise Python
def _ensure_rdpipeline_env():
    try:
        import pydantic
        import rdkit
        return
    except ImportError:
        pass

    candidates = []
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix and os.path.basename(conda_prefix) == "rdpipeline":
        candidates.append(os.path.join(conda_prefix, "bin", "python"))

    candidates.extend([
        os.path.expanduser("~/miniconda3/envs/rdpipeline/bin/python"),
        os.path.expanduser("~/anaconda3/envs/rdpipeline/bin/python"),
        os.path.expanduser("~/.conda/envs/rdpipeline/bin/python"),
    ])

    conda_bin = shutil.which("conda") or os.path.expanduser("~/miniconda3/bin/conda")
    if os.path.isfile(conda_bin):
        try:
            res = subprocess.run([conda_bin, "info", "--base"], capture_output=True, text=True, check=True)
            base = res.stdout.strip()
            candidates.append(os.path.join(base, "envs", "rdpipeline", "bin", "python"))
        except Exception:
            pass

    for py in candidates:
        if os.path.isfile(py) and os.access(py, os.X_OK) and py != sys.executable:
            bin_dir = os.path.dirname(py)
            os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"
            os.execv(py, [py] + sys.argv)


_ensure_rdpipeline_env()

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

    if len(sys.argv) > 1 and sys.argv[1].strip():
        disease_name = sys.argv[1].strip()
        print(f"Disease specified via command line: {disease_name}")
    else:
        try:
            disease_name = input(
                "Enter disease name: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPipeline aborted by user.")
            sys.exit(0)

    if not disease_name:
        print("\n❌ Error: No disease name provided. Exiting.")
        sys.exit(1)

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
