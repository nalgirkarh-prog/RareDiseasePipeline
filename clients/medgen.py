"""
clients/medgen.py

NCBI MedGen connector. MedGen is NCBI's medical-genetics concept database and
is the natural "genetic disease database" bridge between a disease name and its
OMIM id / associated genes.

The original file was empty. This provides a minimal, robust implementation
that fits the rest of the pipeline (uses utils.http, returns plain dicts).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from utils.http import get_json, get_text, polite_pause


class MedGenClient:

    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search_concept(self, disease_name: str) -> dict:
        """
        Search MedGen for a disease and return the top concept's ids.

        Returns a dict like:
            {"medgen_uid": "331172", "disease": "Rett syndrome"}
        or {"disease": ..., "medgen_uid": None} if nothing is found.
        """
        disease_name = str(disease_name).strip()

        search = get_json(
            f"{self.BASE}/esearch.fcgi",
            params={
                "db": "medgen",
                "term": disease_name,
                "retmode": "json",
                "retmax": 1,
            },
        )

        idlist = search.get("esearchresult", {}).get("idlist", [])
        uid = idlist[0] if idlist else None

        return {"disease": disease_name, "medgen_uid": uid}

    def concept_details(self, medgen_uid: str) -> dict:
        """
        Fetch summary details for a MedGen concept id, including any linked
        OMIM id when present.
        """
        polite_pause()

        summary = get_json(
            f"{self.BASE}/esummary.fcgi",
            params={
                "db": "medgen",
                "id": str(medgen_uid),
                "retmode": "json",
            },
        )

        record = summary.get("result", {}).get(str(medgen_uid), {})

        # OMIM ids appear under different keys across NCBI responses;
        # collect whatever is available without assuming a fixed shape.
        omim_id = None
        for key in ("omim", "omimid", "omim_id"):
            value = record.get(key)
            if value:
                omim_id = value[0] if isinstance(value, list) else value
                break

        return {
            "medgen_uid": str(medgen_uid),
            "title": record.get("title"),
            "definition": record.get("definition"),
            "omim_id": omim_id,
        }

    def disease_to_omim(self, disease_name: str) -> dict:
        """Convenience: disease name -> {disease, medgen_uid, omim_id}."""
        concept = self.search_concept(disease_name)
        if not concept.get("medgen_uid"):
            return {**concept, "omim_id": None}
        details = self.concept_details(concept["medgen_uid"])
        return {
            "disease": concept["disease"],
            "medgen_uid": concept["medgen_uid"],
            "omim_id": details.get("omim_id"),
        }
