"""
pipeline/stage10_variant_analysis.py

Variant Impact Analysis stage.

Improvements over the original
--------------------------------
- After building the basic result dict from the Variant model fields, calls
  Ensembl VEP (via EnsemblClient.vep_hgvs) to populate 'consequence' when
  hgvs_c is available.
- Clearly distinguishes "not in ClinVar / no data" (None) from "unknown"
  so the stage result is distinguishable from a stage that never ran.
"""

from __future__ import annotations

from clients.ensembl import EnsemblClient
from modules.variant_analysis import VariantAnalyzer


class VariantAnalysisStage:

    def __init__(self):
        self.analyzer = VariantAnalyzer()
        self.ensembl = EnsemblClient()

    # ------------------------------------------------------------------

    def run(self, variants, protein):
        print("\nAnalyzing variants...")

        analyzed = []

        for variant in variants:
            # --- Consequence: try Ensembl VEP if we have a coding HGVS ---
            consequence = variant.consequence  # may already be set upstream
            if consequence is None and variant.hgvs_c:
                try:
                    consequence = self.ensembl.vep_hgvs(
                        variant.hgvs_c,
                        transcript_id=getattr(variant, "accession", None)
                    )
                    if consequence:
                        print(f"  VEP consequence for {variant.variant_id}: {consequence}")
                except Exception as e:
                    print(f"  ⚠ VEP lookup failed for {variant.variant_id}: {e}")

            # --- Residue: fall back to hgvs_p parsing if not already set ---
            residue = variant.residue
            if residue is None and variant.hgvs_p:
                residue = self.analyzer.extract_residue(variant.hgvs_p)

            result = {
                "variant_id": variant.variant_id,
                "gene": variant.gene,
                "accession": variant.accession,
                "hgvs_c": variant.hgvs_c,
                "hgvs_p": variant.hgvs_p,
                "residue": residue,
                "clinical_significance": variant.clinical_significance,
                "consequence": consequence,
                "mapped": self.analyzer.map_to_sequence(
                    residue,
                    protein.sequence
                ),
                "region": self.analyzer.predict_region(residue),
            }

            analyzed.append(result)

        print(f"Analyzed {len(analyzed)} variants")

        return analyzed
