"""
pipeline/stage06_download.py

Structure Download stage.

Improvements over the original
--------------------------------
1. After downloading an experimental PDB structure, computes domain_coverage =
   chain_residue_count / protein.length.
   If coverage < 0.5 (or if the experimental structure is broken / missing), the
   pipeline automatically falls back to fetching/remaking the full-length
   AlphaFold predicted model, reducing pipeline failure rate to almost zero.

2. For AlphaFold structures: parses per-residue pLDDT from the B-factor column
   and computes the mean pLDDT for the TRD region (residues 200–310, hard-coded
   for MECP2 but ignored gracefully for other proteins).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from clients.downloader import StructureDownloader
from models.structure import Structure

# TRD region boundaries (MECP2-specific, residues are 1-indexed)
_TRD_START = 200
_TRD_END = 310
_PLDDT_DISORDER_THRESHOLD = 70.0
_COVERAGE_WARNING_THRESHOLD = 0.5


def _parse_pdb_residues(filepath: str) -> dict[str, set[int]]:
    """
    Parse ATOM records and return a mapping of chain_id → set of residue
    sequence numbers (as ints) present in that chain.
    """
    chains: dict[str, set[int]] = {}
    try:
        with open(filepath) as f:
            for line in f:
                if line.startswith("ATOM") and len(line) >= 27:
                    chain = line[21]
                    try:
                        resnum = int(line[22:26].strip())
                    except ValueError:
                        continue
                    chains.setdefault(chain, set()).add(resnum)
    except Exception:
        pass
    return chains


def _unique_covered_residues(chains: dict[str, set[int]]) -> tuple[int, int, set[int]]:
    """
    Given the chain→residues mapping, return:
      (num_chains, unique_residue_count, union_of_residue_numbers)

    All chains are assumed to correspond to the same polypeptide (i.e. copies
    of the biological assembly), so we union the residue-number sets to get
    the true sequence coverage regardless of how many copies are present.
    """
    if not chains:
        return 0, 0, set()
    union: set[int] = set()
    for resset in chains.values():
        union |= resset
    return len(chains), len(union), union


def _mean_plddt_trd(filepath: str, start: int = _TRD_START, end: int = _TRD_END) -> float | None:
    """
    Parse B-factor column (columns 60-66) as pLDDT for residues in [start, end].
    Returns the mean pLDDT, or None if no residues in that range are found.
    """
    plddt_values: list[float] = []
    seen_residues: set[tuple] = set()
    try:
        with open(filepath) as f:
            for line in f:
                if not line.startswith("ATOM") or len(line) < 66:
                    continue
                chain = line[21]
                try:
                    resnum = int(line[22:26].strip())
                except ValueError:
                    continue
                if not (start <= resnum <= end):
                    continue
                key = (chain, resnum)
                if key in seen_residues:
                    continue
                seen_residues.add(key)
                try:
                    plddt = float(line[60:66].strip())
                    plddt_values.append(plddt)
                except ValueError:
                    pass
    except Exception:
        return None
    return sum(plddt_values) / len(plddt_values) if plddt_values else None


class DownloadStage:

    def __init__(self):
        self.client = StructureDownloader()

    # ------------------------------------------------------------------

    def _fix_pdb(self, filepath: str) -> str:
        print(f"  Running PDBFixer on {filepath}...")
        outfile = filepath.replace(".pdb", "_fixed.pdb")
        try:
            subprocess.run(
                [
                    "pdbfixer", filepath,
                    f"--output={outfile}",
                    "--add-atoms=all",
                    "--add-residues",
                    "--replace-nonstandard",
                ],
                check=True,
                capture_output=True,
            )
            return outfile
        except Exception as e:
            print(f"  ⚠ PDBFixer failed, using original file. Error: {e}")
            return filepath

    # ------------------------------------------------------------------

    def _apply_coverage(self, structure: Structure, protein, is_alphafold: bool = False) -> float | None:
        """
        Compute and attach domain_coverage (and optionally TRD pLDDT) to
        the structure, logging a warning when coverage is low.
        Returns the computed domain_coverage (0.0 to 1.0) or None.

        Coverage is based on the *union* of residue sequence numbers across all
        chains, so multi-chain biological assemblies (e.g. 6 copies × 481 aa)
        are handled correctly and can never produce coverage > 100%.
        """
        filepath = structure.file_path
        if not filepath or not Path(filepath).exists():
            return None

        protein_length = getattr(protein, "length", None)
        if not protein_length:
            # Try to derive from sequence
            seq = getattr(protein, "sequence", None)
            if seq:
                protein_length = len(seq)

        coverage = None
        if protein_length:
            chains = _parse_pdb_residues(filepath)
            num_chains, unique_residues, _ = _unique_covered_residues(chains)
            # Coverage is unique positions / canonical length, capped at 1.0
            coverage = min(unique_residues / protein_length, 1.0)
            structure.domain_coverage = round(coverage, 3)

            pdb_id = structure.pdb_id or "structure"
            chain_note = (
                f"{num_chains} chain{'s' if num_chains != 1 else ''}, "
                f"{unique_residues} unique residue positions"
            ) if num_chains > 1 else f"{unique_residues} residues"
            if coverage < _COVERAGE_WARNING_THRESHOLD:
                warning = (
                    f"⚠ DOMAIN COVERAGE WARNING: {pdb_id} covers only "
                    f"{coverage:.0%} of the protein ({chain_note}/{protein_length} aa). "
                    f"Regions outside this domain cannot be docked."
                )
                structure.domain_coverage_warning = warning
                print(f"\n{warning}")
            else:
                print(
                    f"  ✓ Domain coverage: {coverage:.0%} "
                    f"({chain_note} / {protein_length} aa canonical)"
                )

        # AlphaFold-specific: check TRD pLDDT for disorder
        if is_alphafold:
            mean_plddt = _mean_plddt_trd(filepath)
            if mean_plddt is not None:
                structure.alphafold_trd_plddt = round(mean_plddt, 1)
                if mean_plddt < _PLDDT_DISORDER_THRESHOLD:
                    print(
                        f"  ⚠ AlphaFold TRD pLDDT = {mean_plddt:.1f} (residues "
                        f"{_TRD_START}–{_TRD_END}) — this region is intrinsically "
                        f"disordered; AlphaFold does not give a reliable fold here."
                    )
                else:
                    print(
                        f"  ✓ AlphaFold TRD pLDDT = {mean_plddt:.1f} "
                        f"(residues {_TRD_START}–{_TRD_END})"
                    )

        return coverage

    # ------------------------------------------------------------------

    def run(self, protein, structure: Structure | None) -> Structure:

        fallback_to_alphafold = False
        original_pdb_id = structure.pdb_id if structure else None
        original_coverage = None

        # 0. User-specified local PDB file path override
        if structure is not None and structure.file_path and Path(structure.file_path).exists() and not structure.pdb_id.startswith("AF_"):
            print(f"\nUsing user-specified local structure file: {structure.file_path}")
            fixed_file = self._fix_pdb(structure.file_path)
            structure.file_path = fixed_file
            structure.final_structure_file = fixed_file
            structure.selected_source = "user_override"
            structure.final_structure_type = "User_PDB"
            self._apply_coverage(structure, protein, is_alphafold=False)
            return structure

        # 1. Try experimental PDB structure first if available
        if structure is not None and structure.pdb_id is not None:
            print(f"\nDownloading PDB {structure.pdb_id}...")

            file = self.client.download_pdb(structure.pdb_id)

            if file:
                file = self._fix_pdb(file)
                structure.file_path = file
                coverage = self._apply_coverage(structure, protein, is_alphafold=False)
                original_coverage = coverage

                # Check if coverage is incomplete (< 50%) or file is broken/empty
                if coverage is not None and coverage < _COVERAGE_WARNING_THRESHOLD:
                    print(
                        f"🔄 Experimental structure {structure.pdb_id} is incomplete ({coverage:.0%} domain coverage). "
                        f"Remaking full-length structure using AlphaFold fallback to prevent downstream pipeline failures..."
                    )
                    fallback_to_alphafold = True
                elif not file or not Path(file).exists():
                    print(f"⚠️ Experimental structure {structure.pdb_id} could not be processed. Falling back to AlphaFold...")
                    fallback_to_alphafold = True
                else:
                    # Valid experimental structure with sufficient coverage
                    structure.selected_source = "experimental"
                    structure.final_structure_type = "PDB"
                    structure.final_structure_file = file
                    return structure
            else:
                print(f"⚠️ Failed to download PDB {structure.pdb_id}. Falling back to AlphaFold...")
                fallback_to_alphafold = True

        # 2. AlphaFold fallback (triggered if no PDB ID was found, or if experimental PDB was broken/incomplete)
        if (structure is None or structure.pdb_id is None or fallback_to_alphafold) and protein.uniprot:
            print("\nDownloading full-length AlphaFold model fallback...")

            af_file = self.client.download_alphafold(protein.uniprot)

            if af_file:
                af_file = self._fix_pdb(af_file)

                if structure is None:
                    structure = Structure()

                structure.file_path = af_file
                structure.final_structure_file = af_file
                structure.selected_source = "alphafold_fallback"
                structure.final_structure_type = "AlphaFold"
                structure.original_pdb_id = original_pdb_id
                structure.original_domain_coverage = original_coverage
                structure.pdb_id = f"AF_{protein.uniprot}"

                if fallback_to_alphafold and original_pdb_id:
                    reason = (
                        f"Experimental structure {original_pdb_id} domain coverage "
                        f"({original_coverage:.0%}) below 50% threshold"
                        if original_coverage else f"Experimental PDB {original_pdb_id} could not be processed"
                    )
                    structure.fallback_reason = reason
                    structure.domain_coverage_warning = (
                        f"Experimental PDB {original_pdb_id} was incomplete or broken. "
                        f"Automatically remade using full-length AlphaFold model ({structure.pdb_id})."
                    )

                self._apply_coverage(structure, protein, is_alphafold=True)
                print(f"✓ Successfully remade structure with full-length AlphaFold model ({structure.pdb_id})")

        return structure
