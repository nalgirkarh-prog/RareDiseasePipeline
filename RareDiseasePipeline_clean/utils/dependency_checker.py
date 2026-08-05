#!/usr/bin/env python3
"""
RareDiseasePipeline v2
Dependency Checker

Checks:
    • Python Version
    • Conda Environment
    • Python Packages
    • External Executables
    • Internet Connection
    • Required Directories

Author: Harsh Nalgirkar
"""

from pathlib import Path
import importlib
import shutil
import socket
import subprocess
import sys


class DependencyChecker:

    def __init__(self):

        self.failed = False

        self.required_packages = {
            "numpy": "NumPy",
            "pandas": "Pandas",
            "Bio": "Biopython",
            "requests": "Requests",
            "yaml": "PyYAML",
            "rdkit": "RDKit",
            "tqdm": "tqdm",
            "rich": "Rich",
            "openbabel": "OpenBabel",
            "pubchempy": "PubChemPy",
            "plip": "PLIP"
        }

        self.executables = {
            "obabel": "Open Babel",
            "vina": "AutoDock Vina",
            "blastp": "BLAST+",
            "hmmscan": "HMMER"
        }

        self.required_dirs = [
            "cache",
            "logs",
            "output",
            "database",
            "config"
        ]

    # --------------------------------------------------

    def ok(self, message):

        print(f"✓ {message}")

    # --------------------------------------------------

    def fail(self, message):

        print(f"✗ {message}")
        self.failed = True

    # --------------------------------------------------

    def check_python(self):

        print("\nChecking Python...")

        if sys.version_info >= (3, 12):
            self.ok(sys.version.split()[0])
        else:
            self.fail("Python >=3.12 required")

    # --------------------------------------------------

    def check_packages(self):

        print("\nChecking Python packages...\n")

        for module, name in self.required_packages.items():

            try:

                importlib.import_module(module)
                self.ok(name)

            except Exception:

                self.fail(name)

    # --------------------------------------------------

    def check_executables(self):

        print("\nChecking external tools...\n")

        for exe, name in self.executables.items():

            if shutil.which(exe):

                self.ok(name)

            else:

                self.fail(name)

    # --------------------------------------------------

    def check_internet(self):

        print("\nChecking Internet...\n")

        try:

            socket.create_connection(("8.8.8.8", 53), timeout=3)

            self.ok("Internet Connection")

        except Exception:

            self.fail("Internet Connection")

    # --------------------------------------------------

    def check_conda(self):

        print("\nChecking Conda...\n")

        result = subprocess.run(
            ["conda", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:

            self.ok(result.stdout.strip())

        else:

            self.fail("Conda")

    # --------------------------------------------------

    def check_directories(self):

        print("\nChecking directories...\n")

        for directory in self.required_dirs:

            path = Path(directory)

            if path.exists():

                self.ok(directory)

            else:

                path.mkdir(parents=True, exist_ok=True)

                print(f"Created {directory}")

    # --------------------------------------------------

    def summary(self):

        print("\n")
        print("=" * 70)

        if self.failed:

            print("Dependency Check FAILED")

            sys.exit(1)

        print("Everything looks good.")
        print("Ready to start RareDiseasePipeline.")

        print("=" * 70)

    # --------------------------------------------------

    def run(self):

        self.check_python()
        self.check_conda()
        self.check_packages()
        self.check_executables()
        self.check_internet()
        self.check_directories()
        self.summary()


if __name__ == "__main__":

    DependencyChecker().run()