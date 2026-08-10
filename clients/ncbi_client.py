"""
clients/ncbi_client.py

Genetic-disease database connector (NCBI Gene, via E-utilities).

This is the client the DiseaseResolver depends on. Given a disease name it
returns the primary associated human gene symbol (e.g. "Rett syndrome" -> "MECP2").

Fixes over the original
-----------------------
1. Robust HTTP: timeouts, retries, backoff, and NCBI api_key/email support
   are all handled by utils.http, so a transient NCBI hiccup no longer kills
   the pipeline.
2. Accepts a Disease object OR a plain string. The original passed the whole
   pydantic Disease object into an f-string, producing a malformed query term
   like "name='Rett syndrome' gene_symbol=None ...[Disease]". Now we always
   extract the .name first.
3. Organism restriction: the search is limited to Homo sapiens so you don't
   get a mouse/zebrafish ortholog by accident.
4. XML parsing is defensive: clear, actionable errors instead of raw
   ElementTree tracebacks.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from utils.http import get_text, get_json, polite_pause, HTTPError


class NCBIGeneClient:

    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_name(disease) -> str:
        """Accept a Disease object, a dict, or a bare string; return the name."""
        if disease is None:
            raise ValueError("No disease supplied to NCBIGeneClient.")
        if isinstance(disease, str):
            name = disease
        elif isinstance(disease, dict):
            name = disease.get("name") or disease.get("disease")
        else:
            name = getattr(disease, "name", None)
        if not name:
            raise ValueError(f"Could not extract a disease name from {disease!r}")
        return str(name).strip()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def disease_to_gene(self, disease) -> str:
        """
        Resolve a disease to its primary human gene symbol.

        Returns the gene symbol as a string (e.g. "MECP2").
        Raises HTTPError on network failure, ValueError on no result.
        """
        disease_name = self._disease_name(disease)

        # Restrict to human genes; [Disease/Phenotype] is the correct E-utilities
        # field for disease association searches.
        term = f'"{disease_name}"[Disease/Phenotype] AND Homo sapiens[Organism]'

        search_json = get_json(
            f"{self.BASE}/esearch.fcgi",
            params={
                "db": "gene",
                "term": term,
                "retmode": "json",
                "retmax": 1,
                "sort": "relevance",
            },
        )

        idlist = (
            search_json
            .get("esearchresult", {})
            .get("idlist", [])
        )

        # Fallback: some diseases index better under the plain [Disease] tag.
        if not idlist:
            polite_pause()
            search_json = get_json(
                f"{self.BASE}/esearch.fcgi",
                params={
                    "db": "gene",
                    "term": f'{disease_name}[Disease] AND Homo sapiens[Organism]',
                    "retmode": "json",
                    "retmax": 1,
                },
            )
            idlist = (
                search_json
                .get("esearchresult", {})
                .get("idlist", [])
            )

        if not idlist:
            raise ValueError(
                f"No human gene associated with '{disease_name}' was found on NCBI."
            )

        gene_id = idlist[0]

        polite_pause()

        # esummary in JSON avoids brittle XML walking.
        summary_json = get_json(
            f"{self.BASE}/esummary.fcgi",
            params={
                "db": "gene",
                "id": gene_id,
                "retmode": "json",
            },
        )

        result = summary_json.get("result", {})
        record = result.get(str(gene_id), {})
        symbol = record.get("name") or record.get("nomenclaturesymbol")

        if not symbol:
            raise ValueError(
                f"Found gene id {gene_id} for '{disease_name}' "
                f"but could not read its symbol."
            )

        return symbol

    # ------------------------------------------------------------------
    # optional: richer resolution used by later stages if desired
    # ------------------------------------------------------------------

    def disease_to_gene_record(self, disease) -> dict:
        """Like disease_to_gene but returns a small dict of useful fields."""
        disease_name = self._disease_name(disease)
        symbol = self.disease_to_gene(disease_name)

        return {
            "disease": disease_name,
            "gene": symbol,
        }
