#!/usr/bin/env python3
"""
RareDiseasePipeline v2
Automatic Environment Installer

Author: Harsh Nalgirkar
"""

from pathlib import Path
import subprocess
import shutil
import sys
import os

ENV_NAME = "rdpipeline"
ENV_FILE = "environment.yml"

REQUIRED_IMPORTS = {
    "numpy": "numpy",
    "pandas": "pandas",
    "Bio": "biopython",
    "rdkit": "rdkit",
    "pydantic": "pydantic",
    "requests": "requests",
    "yaml": "pyyaml",
    "openbabel": "openbabel",
    "pdbfixer": "pdbfixer",
}

# --------------------------------------------------


def banner():
    print("=" * 70)
    print("RareDiseasePipeline Environment Installer")
    print("=" * 70)


# --------------------------------------------------


def run(command):
    print(f"\n>> {' '.join(command)}")

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError("Command failed.")


# --------------------------------------------------


def check_conda():

    if shutil.which("conda") is None:
        print("\nERROR")
        print("Conda was not found.")
        print("Install Miniconda or Anaconda first.")
        sys.exit(1)

    print("✓ Conda detected")


# --------------------------------------------------


def env_exists():

    result = subprocess.run(
        ["conda", "env", "list"],
        capture_output=True,
        text=True,
    )

    return ENV_NAME in result.stdout


# --------------------------------------------------


def create_environment():

    if env_exists():
        print(f"\nEnvironment '{ENV_NAME}' already exists.")
        return

    print("\nCreating environment...\n")

    run([
        "conda",
        "env",
        "create",
        "-f",
        ENV_FILE
    ])


# --------------------------------------------------


def verify_packages():

    print("\nVerifying packages...\n")

    failures = []

    for module, package in REQUIRED_IMPORTS.items():

        command = [
            "conda",
            "run",
            "-n",
            ENV_NAME,
            "python",
            "-c",
            f"import {module}"
        ]

        result = subprocess.run(command)

        if result.returncode == 0:
            print(f"✓ {package}")

        else:
            failures.append(package)
            print(f"✗ {package}")

    return failures


# --------------------------------------------------


def health_report(failures):

    print("\n")
    print("=" * 70)
    print("Health Report")
    print("=" * 70)

    if not failures:

        print("\nEverything looks good.\n")

        print(f"Activate using:\n")
        print(f"conda activate {ENV_NAME}\n")

        print("Happy Research!")

    else:

        print("\nThe following packages failed:\n")

        for pkg in failures:
            print(" -", pkg)

        print("\nPlease reinstall them manually.")


# --------------------------------------------------


def main():

    banner()

    if not Path(ENV_FILE).exists():
        print(f"{ENV_FILE} not found.")
        sys.exit(1)

    check_conda()

    create_environment()

    failures = verify_packages()

    health_report(failures)


# --------------------------------------------------

if __name__ == "__main__":
    main()