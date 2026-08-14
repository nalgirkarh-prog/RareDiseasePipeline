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
    Extract clinical_significance, hgvs_c, hgvs_p from ClinVar esummary.
    Checks germline_classification, clinical_impact_classification, title, and variation_name.
    """
    clin_sig = None

    # 1. Try germline_classification description first (modern ClinVar JSON schema)
    g_class = summary.get("germline_classification", {})
    if isinstance(g_class, dict) and g_class.get("description"):
        clin_sig = g_class["description"].strip()
    elif isinstance(summary.get("clinical_impact_classification"), dict) and summary["clinical_impact_classification"].get("description"):
        clin_sig = summary["clinical_impact_classification"]["description"].strip()
    elif isinstance(summary.get("clinical_significance"), dict) and summary["clinical_significance"].get("description"):
        clin_sig = summary["clinical_significance"]["description"].strip()

    # 2. Extract HGVS expressions from variation_set or title / variation_name
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
            if n_val and n_val.startswith("NM_") and hgvs_c is None:
                hgvs_c = n_val
            if p_val and "p." in p_val and hgvs_p is None:
                hgvs_p = p_val

    # 3. Fallback: Parse from title or variation_name via regex
    title = summary.get("title", "")
    if variation_set and isinstance(variation_set, list) and not title:
        title = variation_set[0].get("variation_name", "")

    if title:
        if not hgvs_c:
            c_match = re.search(r"c\.[0-9a-zA-Z_>+-\.]+", title)
            if c_match:
                hgvs_c = c_match.group(0)
        if not hgvs_p:
            p_match = re.search(r"p\.[0-9a-zA-Z_>+-\.]+", title)
            if p_match:
                hgvs_p = p_match.group(0)

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
        mapped_count = sum(1 for v in variants if v.mapped)
        print(f"✓ Retrieved {len(variants)} ClinVar variants ({mapped_count} mapped with protein-level HGVS for structural analysis)")
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

        for uid in ids[:10]:
            summary = self.client.fetch_esummary(uid)
            parsed = _parse_esummary(summary)

            residue = _extract_residue(parsed["hgvs_p"])
            is_mapped = bool(parsed["hgvs_p"] and residue is not None)

            variant = Variant(
                variant_id=uid,
                gene=symbol,
                accession=uid,
                hgvs_c=parsed["hgvs_c"],
                hgvs_p=parsed["hgvs_p"],
                clinical_significance=parsed["clinical_significance"],
                residue=residue,
                mapped=is_mapped
            )

            sig_str = variant.clinical_significance or "Unclassified"
            hgvs_str = variant.hgvs_p or "no protein HGVS"
            map_str = f"Residue {variant.residue}" if is_mapped else "unmapped"
            print(f"  UID {uid}: {sig_str} | {hgvs_str} ({map_str})")

            variants.append(variant)

        return variants
