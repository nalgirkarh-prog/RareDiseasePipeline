"""
clients/disease/resolver.py

Turns a disease (name / Disease object) into a gene symbol, with a JSON cache
in front of the NCBI call so repeat runs are instant and offline-friendly.

Features:
- Option A (Direct Gene Bypass): If disease has `gene_symbol` specified, returns it directly.
- Option B (Curated HGNC Map): Direct mapping for common disease names and acronyms
  (e.g. DMD -> DMD / HGNC:2928, MECP2, CFTR, etc.) preventing unhandled NCBI string matches.
- JSON cache for fast offline resolution with corrupted-cache protection.
- NCBI Gene E-utilities fallback with clean error handling.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .cache import DiseaseCache
from clients.ncbi_client import NCBIGeneClient
from utils.http import HTTPError


# Curated mapping of common rare diseases, syndromes, and acronyms to HGNC symbols.
KNOWN_DISEASE_MAP = {
    # Muscular dystrophies (DMD / HGNC:2928)
    "dmd": "DMD",
    "duchenne": "DMD",
    "duchenne muscular dystrophy": "DMD",
    "becker muscular dystrophy": "DMD",
    "bmd": "DMD",
    "dystrophin": "DMD",
    # Neurological / Neurodevelopmental
    "rett syndrome": "MECP2",
    "rett": "MECP2",
    "rtt": "MECP2",
    "spinal muscular atrophy": "SMN1",
    "sma": "SMN1",
    "huntington's disease": "HTT",
    "huntington disease": "HTT",
    "huntington": "HTT",
    "hd": "HTT",
    "fragile x syndrome": "FMR1",
    "fragile x": "FMR1",
    "fxs": "FMR1",
    "amyotrophic lateral sclerosis": "SOD1",
    "als": "SOD1",
    "friedreich ataxia": "FXN",
    "friedreich's ataxia": "FXN",
    "fa": "FXN",
    # Metabolic & Genetic
    "cystic fibrosis": "CFTR",
    "cf": "CFTR",
    "phenylketonuria": "PAH",
    "pku": "PAH",
    "wilson disease": "ATP7B",
    "wilson's disease": "ATP7B",
    "fabry disease": "GLA",
    "gaucher disease": "GBA1",
    "marfan syndrome": "FBN1",
    "sickle cell disease": "HBB",
    "sickle cell anemia": "HBB",
    "scd": "HBB",
    "achondroplasia": "FGFR3",
    "neurofibromatosis type 1": "NF1",
    "nf1": "NF1",
}


class DiseaseResolverEngine:

    def __init__(self):
        self.cache = DiseaseCache()
        self.ncbi = NCBIGeneClient()

    @staticmethod
    def _gene_symbol(disease: Any) -> Optional[str]:
        """Extract explicit gene_symbol if set on Disease model or dict."""
        if isinstance(disease, dict):
            sym = disease.get("gene_symbol")
        else:
            sym = getattr(disease, "gene_symbol", None)
        return str(sym).strip().upper() if sym else None

    @staticmethod
    def _name(disease: Any) -> str:
        if isinstance(disease, str):
            return disease.strip()
        name = getattr(disease, "name", None)
        if not name and isinstance(disease, dict):
            name = disease.get("name")
        if not name:
            raise ValueError(f"Cannot resolve disease from {disease!r}")
        return str(name).strip()

    def resolve(self, disease: Any) -> str:
        # 1. Option A: Bypass Resolver if explicit gene symbol provided
        explicit_gene = self._gene_symbol(disease)
        if explicit_gene:
            print(f"✓ Using explicit target gene symbol: {explicit_gene}")
            return explicit_gene

        name = self._name(disease)
        norm_key = name.lower().strip()

        # 2. Option B: Check curated disease/acronym -> HGNC symbol mapping
        if norm_key in KNOWN_DISEASE_MAP:
            gene = KNOWN_DISEASE_MAP[norm_key]
            self.cache.save(norm_key, gene)
            print(f"✓ Mapped '{name}' -> {gene} (via curated disease map / HGNC)")
            return gene

        # 3. Check cache
        cached = self.cache.get(name)
        if cached:
            # Defensive check: ensure DMD is never mapped to ERBB2 from stale cache
            if norm_key in ("dmd", "duchenne", "duchenne muscular dystrophy") and cached.upper() != "DMD":
                print(f"⚠ Stale cache mapping '{name}' -> {cached} detected. Purging...")
                cached = None
            else:
                print(f"✓ '{name}' loaded from cache -> {cached}")
                return cached

        # 4. Fallback to NCBI Gene resolution
        try:
            gene = self.ncbi.disease_to_gene(name)
        except (HTTPError, ValueError) as exc:
            raise RuntimeError(
                f"Disease resolution failed for '{name}': {exc}"
            ) from exc

        self.cache.save(name, gene)
        print(f"✓ Resolved '{name}' -> {gene}")
        return gene
