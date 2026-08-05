"""
clients/fpocket.py

Wrapper around the `fpocket` binary for binding-pocket detection.

Two real-world failures this handles
------------------------------------
1. fpocket lowercases the input basename on some builds. We feed it a lowercase
   name so that is a no-op.

2. fpocket reports  "! File X does not exist"  for a file that IS present when
   the PDB lives on an external / network mount (NTFS, exFAT, fuseblk, or a
   drive mounted noexec). fpocket is a C program using plain fopen(); on those
   mounts the open fails and fpocket prints the misleading "does not exist".

   The robust fix is to run fpocket entirely inside a LOCAL temporary directory
   (under the system tmp, i.e. local disk), then copy the results back next to
   the original PDB. This sidesteps both the mount problem and any path/case
   quirk in one move.

The client returns the path to the original-cased `<STEM>_out` directory placed
next to the input PDB, so the rest of the pipeline is unchanged.
"""

import os
import shutil
import subprocess
import tempfile


class FPocketClient:

    def run(self, pdb_file: str) -> str:
        pdb_file = os.path.abspath(pdb_file)

        if not os.path.exists(pdb_file):
            raise FileNotFoundError(f"{pdb_file} not found.")

        dest_dir = os.path.dirname(pdb_file)
        basename = os.path.basename(pdb_file)          # 1A8M.pdb
        stem = os.path.splitext(basename)[0]           # 1A8M
        low_stem = stem.lower()                        # 1a8m

        # Final output location the pipeline expects (original case, next to PDB)
        final_out = os.path.join(dest_dir, f"{stem}_out")

        # Work in a local temp dir on the system disk, using a lowercase name.
        tmp_root = tempfile.mkdtemp(prefix="fpocket_")
        low_name = f"{low_stem}.pdb"
        tmp_pdb = os.path.join(tmp_root, low_name)
        tmp_out = os.path.join(tmp_root, f"{low_stem}_out")

        try:
            shutil.copy2(pdb_file, tmp_pdb)

            try:
                result = subprocess.run(
                    ["fpocket", "-f", low_name],
                    cwd=tmp_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "fpocket is not installed or not on PATH. "
                    "Install it (e.g. `sudo apt install fpocket` or "
                    "`conda install -c conda-forge fpocket`) and try again."
                ) from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                stdout = (exc.stdout or "").strip()
                raise RuntimeError(
                    f"fpocket failed on {basename} (exit {exc.returncode}).\n"
                    f"stdout: {stdout}\nstderr: {stderr}\n"
                    "Note: if stderr says the file does not exist even though it "
                    "does, the fpocket binary itself may be broken — try "
                    "reinstalling it (sudo apt install fpocket)."
                ) from exc

            if not os.path.isdir(tmp_out):
                stdout = (result.stdout or "").strip()
                raise RuntimeError(
                    "fpocket ran but produced no output directory. The PDB may "
                    f"have no detectable pockets or be malformed.\n"
                    f"fpocket said:\n{stdout}"
                )

            # Normalise the info-file name inside tmp_out to the original case.
            low_info = os.path.join(tmp_out, f"{low_stem}_info.txt")
            up_info = os.path.join(tmp_out, f"{stem}_info.txt")
            if low_info != up_info and os.path.exists(low_info):
                os.replace(low_info, up_info)

            # Copy the whole output back next to the original PDB, original case.
            if os.path.isdir(final_out):
                shutil.rmtree(final_out)
            shutil.copytree(tmp_out, final_out)

            final_info = os.path.join(final_out, f"{stem}_info.txt")
            if not os.path.exists(final_info):
                raise RuntimeError(
                    f"fpocket output is missing its info file ({final_info})."
                )

        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

        return final_out
