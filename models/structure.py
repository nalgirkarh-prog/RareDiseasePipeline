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

    # Mean pLDDT of the TRD region (residues 200–310) in an AlphaFold model.
    # Expected to be low (<70) for intrinsically disordered regions like MECP2 TRD.
    alphafold_trd_plddt: Optional[float] = None
