import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional


# Warning keywords from Open Babel that are scientifically significant
_OBABEL_WARNING_PATTERNS = (
    "kekulize",
    "aromaticity",
    "cannot kekulize",
    "failed to kekulize",
    "invalid smiles",
    "unusual valence",
)


@dataclass
class ReceptorPrepResult:
    """Result returned by ReceptorPreparer.prepare."""
    pdbqt_path: str
    obabel_warnings: list[str] = field(default_factory=list)


class ReceptorPreparer:

    def prepare(self, pdb_file) -> ReceptorPrepResult:

        pdbqt = pdb_file.replace(".pdb", ".pdbqt")

        if os.path.exists(pdbqt):
            return ReceptorPrepResult(pdbqt_path=pdbqt)

        print("Preparing receptor...")

        single_model_pdb = self._extract_first_model(pdb_file)

        result = subprocess.run(

            [
                "obabel",
                single_model_pdb,
                "-O",
                pdbqt,
                "-xr"
            ],

            check=True,
            capture_output=True,
            text=True,

        )

        # Collect scientifically significant warnings from stderr
        warnings: list[str] = []
        for line in (result.stderr or "").splitlines():
            line_lower = line.lower()
            if any(kw in line_lower for kw in _OBABEL_WARNING_PATTERNS):
                warnings.append(line.strip())

        if warnings:
            print(f"  ⚠ Open Babel warnings ({len(warnings)}):")
            for w in warnings:
                print(f"    {w}")

        return ReceptorPrepResult(pdbqt_path=pdbqt, obabel_warnings=warnings)

    def _extract_first_model(self, pdb_file):
        """
        Some PDB entries (e.g. NMR solution structures like 1QK9) contain
        multiple MODEL/ENDMDL blocks representing an ensemble of
        conformers. Vina's rigid-receptor parser only accepts a single
        model, so if the file has more than one, we write out a
        '<id>_model1.pdb' containing just the first model and dock
        against that instead.
        """

        with open(pdb_file) as handle:
            lines = handle.readlines()

        model_count = sum(
            1 for line in lines if line.startswith("MODEL")
        )

        if model_count <= 1:
            return pdb_file

        first_model_lines = []
        in_first_model = False

        for line in lines:

            if line.startswith("MODEL"):
                in_first_model = True
                continue

            if line.startswith("ENDMDL"):
                break

            if in_first_model:
                first_model_lines.append(line)

        first_model_lines.append("END\n")

        output_path = pdb_file.replace(".pdb", "_model1.pdb")

        with open(output_path, "w") as handle:
            handle.writelines(first_model_lines)

        return output_path
