"""
clients/monarch_client.py

Monarch Initiative connector. Given a disease name, returns the top matching
disease concept (id, label, etc.). Useful as a cross-reference / fallback to
NCBI for disease resolution.

Fixes over the original
-----------------------
- Uses utils.http (timeout, retry, backoff) instead of a bare requests.get.
- Returns None-safe results and clear errors.
"""

from __future__ import annotations

from utils.http import get_json, HTTPError


class MonarchClient:

    BASE_URL = "https://api.monarchinitiative.org/v3/api"

    def search_disease(self, disease_name: str) -> dict:
        """
        Return the top Monarch disease match for a name.

        Raises ValueError if nothing matches, HTTPError on network failure.
        """
        disease_name = str(disease_name).strip()

        results = get_json(
            f"{self.BASE_URL}/search",
            params={
                "q": disease_name,
                "category": "biolink:Disease",
                "limit": 1,
            },
        )

        items = results.get("items") or []
        if not items:
            raise ValueError(f"No Monarch disease found for '{disease_name}'")

        return items[0]
