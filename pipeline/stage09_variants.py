"""
pipeline/stage09_variants.py

Variant Retrieval stage.

Improvements over the original
--------------------------------
- Calls ClinVar esummary (JSON) for each UID so that clinical_significance,
  hgvs_c, hgvs_p, and residue are populated with real data instead of being
  hardcoded to "unknown" / None.
- Still falls back gracefully: if a field is not present in the esummary
  response the value stays None (rather than a misleading sentinel).
"""

from __future__ import annotations

import re

from clients.clinvar import ClinVarClient
from models.variant import Variant


def _extract_residue(hgvs_p: str | None) -> int | None:
    """Pull the integer residue number from an HGVS protein string."""
    if not hgvs_p:
        return None
    match = re.search(r"(\d+)", hgvs_p)
    return int(match.group(1)) if match else None


def _parse_esummary(summary: dict) -> dict:
    """
    Extract the fields we care about from a ClinVar esummary DocumentSummary.

    Returns a dict with keys: clinical_significance, hgvs_c, hgvs_p.
    Any field absent from the API response is returned as None (not "unknown").
    """
    # --- clinical significance ---
    clin_sig = None
    sig_block = summary.get("clinical_significance", {})
    if isinstance(sig_block, dict):
        desc = sig_block.get("description")
        if desc:
            clin_sig = desc.strip()

    # --- HGVS expressions ---
    hgvs_c = None
    hgvs_p = None

    variation_set = summary.get("variation_set", [])
    if variation_set and isinstance(variation_set, list):
        variation = variation_set[0].get("variation", {})
        hgvs_list = variation.get("hgvs_expressions", [])
        for expr in hgvs_list:
            if not isinstance(expr, dict):
                continue
            nucleotide = expr.get("nucleotide_expression", {})
            protein = expr.get("protein_expression", {})
            n_val = nucleotide.get("expression", "")
            p_val = protein.get("expression", "")
            # Prefer the NM_ transcript HGVS for coding; avoid NC_ genomic
            if n_val and n_val.startswith("NM_") and hgvs_c is None:
                hgvs_c = n_val
            if p_val and "p." in p_val and hgvs_p is None:
                hgvs_p = p_val

    return {
        "clinical_significance": clin_sig,
        "hgvs_c": hgvs_c,
        "hgvs_p": hgvs_p,
    }


class VariantFetcher:

    def __init__(self):
        self.client = ClinVarClient()

    # ------------------------------------------------------------------

    def run(self, gene) -> list[Variant]:
        print("▶ Fetching variants")
        variants = self.fetch(gene)
        print(f"✓ Retrieved {len(variants)} variants")
        return variants

    # ------------------------------------------------------------------

    def fetch(self, gene) -> list[Variant]:
        print("\nFetching ClinVar variants...")

        symbol = gene.symbol if hasattr(gene, "symbol") else gene

        results = self.client.search_gene(symbol)
        ids = (
            results
            .get("esearchresult", {})
            .get("idlist", [])
        )

        print(f"Found {len(ids)} ClinVar records")

        variants: list[Variant] = []

        for uid in ids[:5]:
            summary = self.client.fetch_esummary(uid)
            parsed = _parse_esummary(summary)

            residue = _extract_residue(parsed["hgvs_p"])

            variant = Variant(
                variant_id=uid,
                gene=symbol,
                accession=uid,
                hgvs_c=parsed["hgvs_c"],
                hgvs_p=parsed["hgvs_p"],
                clinical_significance=parsed["clinical_significance"],
                residue=residue,
            )

            # Log what we actually got so the result is distinguishable
            # from "never ran"
            sig_str = variant.clinical_significance or "not in ClinVar"
            hgvs_str = variant.hgvs_p or "no protein HGVS"
            print(f"  UID {uid}: {sig_str} | {hgvs_str}")

            variants.append(variant)

        return variants
