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

import argparse


def main():

    banner()

    parser = argparse.ArgumentParser(
        description="RareDiseasePipeline - Automated Genomic Drug Discovery Pipeline"
    )
    parser.add_argument(
        "disease",
        nargs="?",
        default=None,
        help="Disease name or acronym (e.g. 'DMD', 'Duchenne muscular dystrophy', 'Rett syndrome')"
    )
    parser.add_argument(
        "--gene", "-g",
        default=None,
        help="Explicit HGNC gene symbol to bypass resolver (e.g. 'DMD', 'MECP2')"
    )
    parser.add_argument(
        "--max-stage", "-s",
        type=int,
        default=None,
        help="Maximum pipeline stage index to execute (0-16). E.g. 10 for Stages 00-10"
    )
    parser.add_argument(
        "--non-interactive", "-y",
        action="store_true",
        help="Run without interactive Human-in-the-Loop prompts"
    )

    args = parser.parse_args()

    disease_name = args.disease
    gene_symbol = args.gene.strip().upper() if args.gene else None

    if disease_name and disease_name.strip():
        disease_name = disease_name.strip()
        print(f"Disease specified via command line: {disease_name}")
    elif not gene_symbol:
        try:
            disease_name = input(
                "Enter disease name: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPipeline aborted by user.")
            sys.exit(0)
    else:
        disease_name = gene_symbol

    if not disease_name and not gene_symbol:
        print("\n❌ Error: No disease name or gene symbol provided. Exiting.")
        sys.exit(1)

    if gene_symbol:
        print(f"Explicit target gene specified: {gene_symbol}")

    print(
        f"\n🧬 Initializing project for: {disease_name} (Gene: {gene_symbol or 'auto-resolve'})\n"
    )

    # Create disease object (with explicit gene_symbol if supplied)
    project = Disease(
        name=disease_name,
        gene_symbol=gene_symbol
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
            interactive=(not args.non_interactive and args.max_stage is None),
            max_stage=args.max_stage
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
