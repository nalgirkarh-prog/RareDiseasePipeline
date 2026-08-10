#!/usr/bin/env python3
"""
RareDiseasePipeline v2
Environment Updater

Updates both Conda and pip packages,
cleans cache, verifies installation,
and prints a health report.
"""

import shutil
import subprocess
import sys

ENV_NAME = "rdpipeline"


def banner():
    print("=" * 70)
    print("RareDiseasePipeline Environment Updater")
    print("=" * 70)


def run(cmd):

    print("\n>>", " ".join(cmd))

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\nCommand failed.")
        return False

    return True


def check_conda():

    if shutil.which("conda") is None:
        print("Conda not found.")
        sys.exit(1)


def update_conda():

    print("\nUpdating conda packages...")

    run([
        "conda",
        "update",
        "-n",
        ENV_NAME,
        "--all",
        "-y"
    ])


def update_pip():

    print("\nChecking outdated pip packages...")

    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            ENV_NAME,
            "python",
            "-m",
            "pip",
            "list",
            "--outdated",
            "--format=freeze"
        ],
        capture_output=True,
        text=True,
    )

    packages = []

    for line in result.stdout.splitlines():

        if "==" in line:
            packages.append(line.split("==")[0])

    if not packages:

        print("Everything is already up-to-date.")
        return

    print("\nUpdating pip packages...\n")

    for pkg in packages:

        run([
            "conda",
            "run",
            "-n",
            ENV_NAME,
            "python",
            "-m",
            "pip",
            "install",
            "--upgrade",
            pkg
        ])


def clean():

    print("\nCleaning conda cache...\n")

    run([
        "conda",
        "clean",
        "--all",
        "-y"
    ])


def verify():

    modules = [
        "numpy",
        "pandas",
        "Bio",
        "rdkit",
        "requests",
        "yaml"
    ]

    print("\nVerifying installation...\n")

    failures = []

    for module in modules:

        result = subprocess.run(
            [
                "conda",
                "run",
                "-n",
                ENV_NAME,
                "python",
                "-c",
                f"import {module}"
            ]
        )

        if result.returncode == 0:

            print(f"✓ {module}")

        else:

            print(f"✗ {module}")
            failures.append(module)

    return failures


def report(failures):

    print("\n")
    print("=" * 70)

    if failures:

        print("Update completed with warnings.\n")

        for module in failures:
            print("-", module)

    else:

        print("Environment successfully updated.")
        print("Everything looks healthy.")

    print("=" * 70)


def main():

    banner()

    check_conda()

    update_conda()

    update_pip()

    clean()

    failures = verify()

    report(failures)


if __name__ == "__main__":
    main()