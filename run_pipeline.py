#!/usr/bin/env python3
"""
Interactive launcher for RareDiseasePipeline.

Features:
- Automatically locates the 'rdpipeline' Conda environment Python even if
  system Python or another version manager (like mise) is active in the shell.
- Passes interactive stdin/stdout directly, allowing you to enter any disease name
  and interact with Human-in-the-Loop choices (execution depth, structure selection).
- Supports passing the disease name as an optional command-line argument:
    ./run_pipeline.py "Wilson Disease"
  or running without arguments to be prompted interactively:
    ./run_pipeline.py
"""

import os
import shutil
import subprocess
import sys


def find_rdpipeline_python() -> str:
    # 1. If current python already has rdpipeline dependencies installed
    try:
        import pydantic
        import rdkit
        return sys.executable
    except ImportError:
        pass

    # 2. Check CONDA_PREFIX
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix and os.path.basename(conda_prefix) == "rdpipeline":
        py = os.path.join(conda_prefix, "bin", "python")
        if os.path.isfile(py) and os.access(py, os.X_OK):
            return py

    # 3. Known standard conda environment paths
    candidates = [
        os.path.expanduser("~/miniconda3/envs/rdpipeline/bin/python"),
        os.path.expanduser("~/anaconda3/envs/rdpipeline/bin/python"),
        os.path.expanduser("~/.conda/envs/rdpipeline/bin/python"),
    ]
    for cand in candidates:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand

    # 4. Try discovery via conda executable
    conda_bin = shutil.which("conda") or os.path.expanduser("~/miniconda3/bin/conda")
    if os.path.isfile(conda_bin):
        try:
            res = subprocess.run(
                [conda_bin, "info", "--base"],
                capture_output=True,
                text=True,
                check=True
            )
            base = res.stdout.strip()
            cand = os.path.join(base, "envs", "rdpipeline", "bin", "python")
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
        except Exception:
            pass

    return sys.executable


def main():
    target_python = find_rdpipeline_python()

    # Prepend the environment's bin directory to PATH so tools like vina, fpocket, etc. are found
    env = dict(os.environ)
    bin_dir = os.path.dirname(target_python)
    if bin_dir:
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    cmd = [target_python, main_py] + sys.argv[1:]

    try:
        proc = subprocess.run(cmd, env=env)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()

