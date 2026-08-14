from pydantic import BaseModel
from typing import Optional


class Structure(BaseModel):

    pdb_id: Optional[str] = None

    title: Optional[str] = None

    method: Optional[str] = None

    resolution: Optional[float] = None

    file_path: Optional[str] = None

    # Fraction of the full-length protein covered by this structure (0.0–1.0).
    # < 0.5 triggers a domain-only coverage warning.
    domain_coverage: Optional[float] = None

    # Human-readable warning when domain_coverage is low, e.g.:
    # "1QK9 covers only 17% of MECP2 (498 aa). TRD region not present."
    domain_coverage_warning: Optional[str] = None

    # Mean pLDDT score for AlphaFold predictions in TRD region (or overall)
    alphafold_trd_plddt: Optional[float] = None

    # Explicit structure provenance tracking:
    selected_source: Optional[str] = "experimental"  # "experimental", "alphafold_fallback", or "user_override"
    original_pdb_id: Optional[str] = None
    original_domain_coverage: Optional[float] = None
    final_structure_file: Optional[str] = None
    final_structure_type: Optional[str] = "PDB"  # "PDB", "AlphaFold", or "User_PDB"
    fallback_reason: Optional[str] = None
