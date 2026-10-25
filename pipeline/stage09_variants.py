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
from utils.http import polite_pause


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

    # 4. Extract variation_type from variation_set or top-level obj_type
    variation_type = None
    if variation_set and isinstance(variation_set, list):
        vt = variation_set[0].get("variation_type")
        if vt:
            variation_type = str(vt).strip()
    if not variation_type:
        obj_type = summary.get("obj_type")
        if obj_type:
            variation_type = str(obj_type).strip()

    return {
        "clinical_significance": clin_sig,
        "hgvs_c": hgvs_c,
        "hgvs_p": hgvs_p,
        "variation_type": variation_type,
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

        # 1. Pathogenic / Likely pathogenic variants first (up to 100)
        path_results = self.client.search_gene_pathogenic(symbol)
        path_ids = (
            path_results
            .get("esearchresult", {})
            .get("idlist", [])
        )
        print(f"Found {len(path_ids)} Pathogenic/Likely pathogenic ClinVar records")
        polite_pause()

        # 2. Broader set (up to 500)
        all_results = self.client.search_gene(symbol)
        all_ids = (
            all_results
            .get("esearchresult", {})
            .get("idlist", [])
        )
        print(f"Found {len(all_ids)} total ClinVar records")

        # 3. Combine: pathogenic first, deduplicated, cap at 50
        seen: set[str] = set()
        combined_ids: list[str] = []
        for uid in path_ids + all_ids:
            if uid not in seen:
                seen.add(uid)
                combined_ids.append(uid)
        combined_ids = combined_ids[:50]
        print(f"Processing {len(combined_ids)} variants (pathogenic-prioritised, deduped)")

        variants: list[Variant] = []
        sig_counts: dict[str, int] = {}

        for i, uid in enumerate(combined_ids):
            if i > 0 and i % 10 == 0:
                print(f"  ... processed {i}/{len(combined_ids)} variants")

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
                variation_type=parsed["variation_type"],
                residue=residue,
                mapped=is_mapped
            )

            sig_label = variant.clinical_significance or "Unclassified"
            sig_counts[sig_label] = sig_counts.get(sig_label, 0) + 1

            hgvs_str = variant.hgvs_p or "no protein HGVS"
            map_str = f"Residue {variant.residue}" if is_mapped else "unmapped"
            print(f"  UID {uid}: {sig_label} | {hgvs_str} ({map_str})")

            variants.append(variant)

        # 4. Summary by clinical significance
        print("\n  Clinical significance summary:")
        for sig, count in sorted(sig_counts.items(), key=lambda x: -x[1]):
            print(f"    {sig}: {count}")

        return variants
