"""
clients/clinvar.py

ClinVar connector (NCBI). Given a gene symbol, returns the ClinVar variant
UIDs and can fetch individual variant records.

Fixes over the original
-----------------------
- Uses utils.http for timeouts, retries, backoff and NCBI api_key/email.
  The original hand-rolled a partial retry loop only for efetch and left
  esearch with no timeout at all.
- Consistent, readable errors.
"""

from __future__ import annotations

from utils.http import get_json, get_text, polite_pause, HTTPError


class ClinVarClient:

    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search_gene(self, gene: str) -> dict:
        """Return the raw ClinVar esearch JSON for a gene symbol."""
        gene = str(gene).strip()

        result = get_json(
            f"{self.BASE}/esearch.fcgi",
            params={
                "db": "clinvar",
                "term": f"{gene}[gene]",
                "retmode": "json",
                "retmax": 20,
            },
        )
        polite_pause()
        return result

    def variant_ids(self, gene: str) -> list[str]:
        """Convenience: gene -> list of ClinVar UIDs."""
        data = self.search_gene(gene)
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_variant(self, uid: str) -> str:
        """Fetch a single ClinVar variant record as XML text."""
        text = get_text(
            f"{self.BASE}/efetch.fcgi",
            params={
                "db": "clinvar",
                "id": str(uid),
                "retmode": "xml",
            },
        )
        polite_pause()
        return text
