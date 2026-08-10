import os
import re
import subprocess
from pathlib import Path


class VinaClient:

    def dock(self, receptor, ligand, box, seed: int = None):

        ligand_name = Path(ligand).stem

        docking_dir = Path("output") / "docking" / ligand_name
        docking_dir.mkdir(parents=True, exist_ok=True)

        pose_file = docking_dir / "pose.pdbqt"
        log_file = docking_dir / "docking.log"

        command = [
            "vina",
            "--receptor", receptor,
            "--ligand", ligand,
            "--center_x", str(box["center_x"]),
            "--center_y", str(box["center_y"]),
            "--center_z", str(box["center_z"]),
            "--size_x", str(box["size_x"]),
            "--size_y", str(box["size_y"]),
            "--size_z", str(box["size_z"]),
            "--out", str(pose_file),
            "--exhaustiveness", "24",
            "--num_modes", "5",
        ]

        # Optional seed for reproducibility (Fix 4)
        if seed is not None:
            command.extend(["--seed", str(seed)])

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        with open(log_file, "w") as f:
            f.write(result.stdout)

            if result.stderr:
                f.write("\n\nSTDERR\n")
                f.write(result.stderr)

        if result.returncode != 0:
            raise RuntimeError(f"Docking failed for {ligand_name}")

        affinity = self.extract_affinity(result.stdout)

        aff_str = f"{affinity:.2f} kcal/mol" if affinity is not None else "N/A"
        print(f"   ✓ {ligand_name}   {aff_str}")

        return {
            "ligand_name": ligand_name,
            "affinity": affinity,
            "pose": str(pose_file),
            "log": str(log_file)
        }


    def extract_affinity(self, output):

        for line in output.splitlines():

            match = re.search(r"^\s*1\s+([+-]?\d+\.\d+)", line)

            if match:
                return float(match.group(1))

        return None

