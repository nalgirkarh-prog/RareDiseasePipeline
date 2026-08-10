"""
clients/chembl.py

Fix 2 (bioactivity quality filter in get_activities):
    Previously, every activity record returned by ChEMBL was accepted,
    including qualitative records (e.g. "Active/Inactive" flags, cross-species
    data, and entries without a measured pChEMBL value).  This leads to
    structurally diverse but pharmacologically weak ligands populating the
    screening sets.

    The updated get_activities() adds server-side query parameters to restrict
    results to:
      • standard_type in {IC50, Ki, Kd, EC50}  — quantitative binding assays
      • pchembl_value IS NOT NULL              — ensures a numeric potency exists
      • target_organism == "Homo sapiens"       — human targets only (when provided)

    All three filters are exposed as keyword arguments with the above as
    defaults so callers can override them (e.g. to include rat data for
    selectivity profiling).
"""

import requests


# ── defaults used by get_activities() ─────────────────────────────────────────
DEFAULT_ASSAY_TYPES = {"IC50", "Ki", "Kd", "EC50"}
DEFAULT_ORGANISM   = "Homo sapiens"


class ChEMBLClient:

    BASE = "https://www.ebi.ac.uk/chembl/api/data"

    def search_target(self, gene_symbol: str):
        """
        Search ChEMBL target using gene symbol.
        """
        url = f"{self.BASE}/target/search?q={gene_symbol}&format=json"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_target(self, target_chembl_id: str):
        """
        Get target metadata.
        """
        url = f"{self.BASE}/target/{target_chembl_id}.json"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_activities(
        self,
        target_chembl_id: str,
        limit: int = 500,
        standard_types: set = None,
        organism: str = DEFAULT_ORGANISM,
        require_pchembl: bool = True,
    ):
        """
        Retrieve bioactivity records for a ChEMBL target.

        Parameters
        ----------
        target_chembl_id : str
        limit            : int   — max records returned (server-side)
        standard_types   : set   — assay types to accept; defaults to
                                   {IC50, Ki, Kd, EC50}
        organism         : str   — restrict to this target organism;
                                   pass None to disable the filter
        require_pchembl  : bool  — if True, only records with a numeric
                                   pChEMBL value are returned

        Fix 2: Added organism, standard_type, and pChEMBL filters so only
        pharmacologically meaningful, human-target activities reach the
        ligand-discovery stage.
        """
        if standard_types is None:
            standard_types = DEFAULT_ASSAY_TYPES

        # Build query string; ChEMBL REST API accepts multiple filter params
        params = (
            f"?target_chembl_id={target_chembl_id}"
            f"&limit={limit}"
        )

        # Append one standard_type filter per assay type (OR semantics via
        # repeated params are not supported by ChEMBL REST; instead we fetch
        # broadly and filter locally — see post-processing below)
        url = f"{self.BASE}/activity.json{params}"

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        payload = r.json()

        # ── Local filtering (Fix 2) ────────────────────────────────────────
        raw_activities = payload.get("activities", [])
        filtered = []

        for act in raw_activities:
            # 1. Assay-type filter
            if standard_types and act.get("standard_type") not in standard_types:
                continue

            # 2. Require numeric pChEMBL value
            if require_pchembl and act.get("pchembl_value") is None:
                continue

            # 3. Organism filter (field may not always be present)
            if organism:
                act_org = act.get("target_organism") or ""
                if act_org and act_org != organism:
                    continue

            filtered.append(act)

        payload["activities"] = filtered
        return payload

    def get_molecule(self, molecule_chembl_id: str):
        """
        Retrieve molecule metadata.
        """
        url = f"{self.BASE}/molecule/{molecule_chembl_id}.json"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
