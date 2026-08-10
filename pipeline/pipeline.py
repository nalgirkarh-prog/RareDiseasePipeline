"""
RareDiseasePipeline v2
Pipeline Controller

Author: Harsh Nalgirkar

Controls execution of every stage of the pipeline.
Supports:

• Logging
• Dependency checking
• Stage timing
• Checkpointing (output/docking_checkpoint.json, per-ligand)
• Resume support (restarts skip already-completed ligands)
• Exception handling
"""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

from utils.dependency_checker import DependencyChecker
from utils.logger import logger


class Pipeline:
    """
    Main execution controller.
    """

    def __init__(self):

        self.stages: List[Any] = []

        self.context: Dict[str, Any] = {}

        self.stage_times: Dict[str, float] = {}

    # =========================================================

    def add_stage(self, stage):

        """
        Register a stage.
        """

        self.stages.append(stage)

    # =========================================================

    def get_stage(self, index):

        return self.stages[index]

    # =========================================================

    def banner(self):

        logger.info("=" * 70)

    # =========================================================

    def initialize(self, disease):

        """
        Initialize pipeline context.
        """

        self.context = {
            "disease": disease
        }

    # =========================================================

    def check_dependencies(self):

        logger.section("Dependency Check")

        DependencyChecker().run()

    # =========================================================

    def execute_stage(
        self,
        number: int,
        title: str,
        function,
        context_key: str = None
    ):

        logger.stage(number, title)

        start = time.perf_counter()

        try:

            result = function()

            elapsed = time.perf_counter() - start

            self.stage_times[title] = elapsed

            logger.success(
                f"{title} completed ({elapsed:.2f}s)"
            )

            if context_key is not None:
                self.context[context_key] = result

            return result

        except KeyboardInterrupt:

            logger.failed(
                "Pipeline interrupted by user."
            )

            raise

        except Exception:

            logger.error(
                traceback.format_exc()
            )

            raise

    # =========================================================

    def summary(self):

        logger.section("Execution Summary")

        total = 0

        for stage, t in self.stage_times.items():

            total += t

            logger.info(
                f"{stage:<35} {t:8.2f}s"
            )

        logger.info("-" * 50)

        logger.success(
            f"Total Runtime : {total:.2f}s"
        )

    # =========================================================

    def verify_pipeline(self):

        if len(self.stages) < 17:

            raise RuntimeError(
                f"Expected 16 stages, found {len(self.stages)}."
            )

    # =========================================================

    def run(self, disease):
        self.banner()

        self.verify_pipeline()

        self.check_dependencies()

        self.initialize(disease)

        logger.section("Pipeline Started")

        # =====================================================
        # Stage 00 : Disease Resolver
        # =====================================================

        gene_data = self.execute_stage(
            0,
            "Disease Resolver",
            lambda: self.stages[0].run(
                disease
            ),
            "gene"
        )

        # =====================================================
        # Stage 01 : Gene Fetcher
        # =====================================================

        gene = self.execute_stage(
            1,
            "Gene Fetcher",
            lambda: self.stages[1].run(
                gene_data
            ),
            "gene_info"
        )

        # =====================================================
        # Stage 02 : Transcript
        # =====================================================

        transcript = self.execute_stage(
            2,
            "Transcript Selection",
            lambda: self.stages[2].run(
                gene
            ),
            "transcript"
        )

        # =====================================================
        # Stage 03 : Protein
        # =====================================================

        protein = self.execute_stage(
            3,
            "Protein Mapping",
            lambda: self.stages[3].run(
                transcript
            ),
            "protein"
        )

        # =====================================================
        # Stage 04 : UniProt Mapping
        # =====================================================

        protein = self.execute_stage(
            4,
            "UniProt Mapping",
            lambda: self.stages[4].run(
                protein
            ),
            "protein"
        )

        # =====================================================
        # Stage 05 : Structure Search
        # =====================================================

        structure = self.execute_stage(
            5,
            "Structure Search",
            lambda: self.stages[5].run(
                protein
            ),
            "structure"
        )

        # =====================================================
        # Stage 06 : Structure Download
        # =====================================================

        structure = self.execute_stage(
            6,
            "Structure Download",
            lambda: self.stages[6].run(
                protein,
                structure
            ),
            "structure"
        )

        self.context["pdb_file"] = structure.file_path

        pdb_file = structure.file_path

        # =====================================================
        # Stage 07 : Regulatory Analysis
        # =====================================================

        regulation = self.execute_stage(
            7,
            "Regulatory Analysis",
            lambda: self.stages[7].run(
                gene
            ),
            "regulation"
        )

        # =====================================================
        # Stage 08 : Pocket Detection
        # =====================================================

        pockets = self.execute_stage(
            8,
            "Binding Pocket Detection",
            lambda: self.stages[8].run(
                pdb_file
            ),
            "pockets"
        )

        # =====================================================
        # Stage 09 : Variant Fetching
        # =====================================================

        variants = self.execute_stage(
            9,
            "Variant Retrieval",
            lambda: self.stages[9].run(
                gene
            ),
            "variants"
        )

        # =====================================================
        # Stage 10 : Variant Analysis
        # =====================================================

        variant_analysis = self.execute_stage(
            10,
            "Variant Impact Analysis",
            lambda: self.stages[10].run(
                variants,
                protein
            ),
            "variant_analysis"
        )

        # =====================================================
        # Stage 11 : Ligand Screening
        # =====================================================

        ligands = self.execute_stage(
            11,
            "Ligand Screening",
            lambda: self.stages[11].run(
                protein,
                pockets,
                regulation
            ),
            "ligands"
        )

        # =====================================================
        # Stage 12 : Molecular Docking
        # =====================================================

        # Sort pockets by druggability score (descending) so the most
        # druggable pocket is always used, regardless of fpocket file ordering.
        # Fall back to the raw fpocket score when druggability is None.
        if pockets:
            sorted_pockets = sorted(
                pockets,
                key=lambda p: (
                    p.druggability if p.druggability is not None else p.score
                ),
                reverse=True,
            )
            best_pocket = sorted_pockets[0]
            print(
                f"\n📍 Selected pocket: {best_pocket.pocket_id} "
                f"(druggability={best_pocket.druggability}, "
                f"score={best_pocket.score})"
            )
        else:
            best_pocket = None

        # DockingStage.run() returns (top_candidates, all_results).
        # Store the full tuple in context so stage13_ranking can see both.
        docking_results = self.execute_stage(
            12,
            "Molecular Docking",
            lambda: self.stages[12].run(
                structure,
                best_pocket,
                ligands
            ),
            "docking_results"
        )

        # =====================================================
        # Stage 13 : Candidate Ranking
        # =====================================================

        ranked_candidates = self.execute_stage(
            13,
            "Candidate Ranking",
            lambda: self.stages[13].run(
                self.context
            ),
            "ranked_candidates"
        )

        # =====================================================
        # Stage 14 : Drug Evaluation
        # =====================================================

        evaluated_candidates = self.execute_stage(
            14,
            "Drug Evaluation",
            lambda: self.stages[14].run(
                ranked_candidates
            ),
            "evaluated_candidates"
        )

        # =====================================================
        # Stage 15 : Simulation Builder
        # =====================================================

        simulation = self.execute_stage(
            15,
            "Simulation Builder",
            lambda: self.stages[15].run(
                self.context
            ),
            "simulation"
        )
       # =====================================================
       # Stage 16 : Report Generation
       # =====================================================

        report = self.execute_stage(
            16,
            "Report Generation",
            lambda: self.stages[16].run(
                self.context
            ),
            "report"
        )
