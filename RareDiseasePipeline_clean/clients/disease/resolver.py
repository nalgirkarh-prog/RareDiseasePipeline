"""
clients/disease/resolver.py

Turns a disease (name / Disease object) into a gene symbol, with a JSON cache
in front of the NCBI call so repeat runs are instant and offline-friendly.

Fixes over the original
-----------------------
- Always resolves the disease *name* before hitting NCBI (the old code passed
  the whole Disease object through, which produced a malformed query term).
- Caches the resolved gene under the normalised disease name, and the cache
  read/write now use the same key, so cache hits actually work.
- A cached but empty/failed value is ignored and re-fetched.
"""

from .cache import DiseaseCache
from clients.ncbi_client import NCBIGeneClient
from utils.http import HTTPError


class DiseaseResolverEngine:

    def __init__(self):
        self.cache = DiseaseCache()
        self.ncbi = NCBIGeneClient()

    @staticmethod
    def _name(disease) -> str:
        if isinstance(disease, str):
            return disease.strip()
        name = getattr(disease, "name", None)
        if not name and isinstance(disease, dict):
            name = disease.get("name")
        if not name:
            raise ValueError(f"Cannot resolve disease from {disease!r}")
        return str(name).strip()

    def resolve(self, disease) -> str:
        name = self._name(disease)

        cached = self.cache.get(name)
        if cached:
            print(f"\u2713 '{name}' loaded from cache -> {cached}")
            return cached

        try:
            gene = self.ncbi.disease_to_gene(name)
        except (HTTPError, ValueError) as exc:
            # Surface a clean, actionable message instead of a raw traceback.
            raise RuntimeError(
                f"Disease resolution failed for '{name}': {exc}"
            ) from exc

        self.cache.save(name, gene)
        print(f"\u2713 Resolved '{name}' -> {gene}")
        return gene
