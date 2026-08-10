"""
modules/pocket_analysis.py

Parses fpocket's _info.txt output and returns a list of Pocket objects.

Improvements over the original
--------------------------------
- After constructing each Pocket from the info file, calls PocketGeometry to
  compute center_x/y/z and size_x/y/z from the pocket's _vert.pqr alpha-sphere
  file, so those fields are never left as None when fpocket has run.
- Fails gracefully: if the .pqr file is missing or empty the geometry fields
  remain None and a warning is printed rather than crashing.
"""

from __future__ import annotations

import os
import re

from models.pocket import Pocket
from modules.pocket_geometry import PocketGeometry


class PocketAnalyzer:

    def __init__(self):
        self._geometry = PocketGeometry()

    # ------------------------------------------------------------------

    def parse_info(self, info_file: str, pocket_folder: str) -> list[Pocket]:
        pockets: list[Pocket] = []

        with open(info_file) as f:
            content = f.read()

        blocks = content.split("Pocket ")[1:]

        for i, block in enumerate(blocks, start=1):

            def extract(pattern: str, b: str = block):
                match = re.search(pattern, b)
                if match:
                    return float(match.group(1))
                return None

            atm_file = f"{pocket_folder}/pocket{i}_atm.pdb"
            pqr_file = f"{pocket_folder}/pocket{i}_vert.pqr"

            pocket = Pocket(
                pocket_id=f"pocket{i}",
                score=extract(r"Score\s+:\s+([\d\.\-]+)"),
                druggability=extract(r"Druggability Score\s+:\s+([\d\.\-]+)"),
                volume=extract(r"Volume\s+:\s+([\d\.\-]+)"),
                source_file=atm_file,
            )

            # Compute center and bounding box from alpha-sphere coordinates
            if os.path.exists(pqr_file):
                try:
                    geo = self._geometry.calculate(pqr_file)
                    pocket.center_x = geo["center_x"]
                    pocket.center_y = geo["center_y"]
                    pocket.center_z = geo["center_z"]
                    pocket.size_x = geo["size_x"]
                    pocket.size_y = geo["size_y"]
                    pocket.size_z = geo["size_z"]
                except Exception as e:
                    print(
                        f"  ⚠ Could not compute geometry for pocket{i} "
                        f"({pqr_file}): {e}"
                    )
            else:
                print(
                    f"  ⚠ Vertex file not found for pocket{i}: {pqr_file} — "
                    f"center/size will be None"
                )

            pockets.append(pocket)

        return pockets
