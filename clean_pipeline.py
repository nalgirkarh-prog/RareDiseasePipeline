#!/usr/bin/env python3
"""
clean_pipeline.py — Reset the RareDiseasePipeline workspace

Removes all generated output, cached data, and scratch files so the
pipeline can be re-run for a new disease from a clean slate.

Usage:
    python clean_pipeline.py           # interactive — shows plan, asks to confirm
    python clean_pipeline.py --yes     # skip confirmation
    python clean_pipeline.py --dry-run # just show what would be deleted
    python clean_pipeline.py --keep-cache  # keep database downloads & cache
"""

import argparse
import shutil
import sys
from pathlib import Path


# ── Project root is wherever this script lives ──────────────────────────
ROOT = Path(__file__).resolve().parent


# ── Targets to clean ────────────────────────────────────────────────────

# Directories to remove entirely
DIRS_TO_REMOVE = [
    "simulations",
    "output/docking",
    "output/ligands",
    "logs",
]

# Files (globs) in the output/ directory
OUTPUT_FILE_GLOBS = [
    "output/*.csv",
    "output/*.json",
]

# Antechamber / sqm scratch files left in the project root
ROOT_SCRATCH_GLOBS = [
    "ANTECHAMBER_*.AC",
    "ANTECHAMBER_*.AC0",
    "ATOMTYPE.INF",
    "sqm.in",
    "sqm.out",
    "sqm.pdb",
    "test.pdb",
    "leap.log",
    "*.acpype",           # acpype output directories
]

# Cache / database (skipped with --keep-cache)
CACHE_TARGETS = [
    "cache/disease_cache.json",
    "database/pdb",
    "database/structures",
]

# Python bytecode caches (always cleaned)
PYCACHE_DIR_NAME = "__pycache__"


# ── Helpers ─────────────────────────────────────────────────────────────

def collect_targets(keep_cache: bool):
    """Return a list of (Path, kind) tuples to be removed."""
    targets = []

    # 1. Directories
    for d in DIRS_TO_REMOVE:
        p = ROOT / d
        if p.exists():
            targets.append((p, "directory"))

    # 2. Output file globs
    for pattern in OUTPUT_FILE_GLOBS:
        for p in ROOT.glob(pattern):
            targets.append((p, "file"))

    # 3. Root scratch globs
    for pattern in ROOT_SCRATCH_GLOBS:
        for p in ROOT.glob(pattern):
            kind = "directory" if p.is_dir() else "file"
            targets.append((p, kind))

    # 4. Cache / database (unless --keep-cache)
    if not keep_cache:
        for entry in CACHE_TARGETS:
            p = ROOT / entry
            if p.exists():
                kind = "directory" if p.is_dir() else "file"
                targets.append((p, kind))

    # 5. __pycache__ everywhere
    for p in ROOT.rglob(PYCACHE_DIR_NAME):
        if p.is_dir():
            targets.append((p, "directory"))

    return targets


def pretty_path(p: Path) -> str:
    """Display path relative to ROOT for readability."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def print_plan(targets):
    """Print a human-readable deletion plan."""
    if not targets:
        print("\n✅ Workspace is already clean — nothing to remove.\n")
        return

    dirs = [(p, k) for p, k in targets if k == "directory"]
    files = [(p, k) for p, k in targets if k == "file"]

    total_size = 0
    for p, k in targets:
        if p.is_file():
            total_size += p.stat().st_size
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

    print("\n" + "=" * 56)
    print("  🧹  Pipeline Cleanup Plan")
    print("=" * 56)

    if dirs:
        print(f"\n  Directories to remove ({len(dirs)}):")
        for p, _ in dirs:
            print(f"    📁 {pretty_path(p)}/")

    if files:
        print(f"\n  Files to remove ({len(files)}):")
        for p, _ in files:
            print(f"    📄 {pretty_path(p)}")

    size_mb = total_size / (1024 * 1024)
    print(f"\n  Total: {len(targets)} items  (~{size_mb:.1f} MB)")
    print("=" * 56)


def execute_cleanup(targets):
    """Actually delete the targets."""
    removed = 0
    errors = 0

    for p, kind in targets:
        try:
            if kind == "directory" and p.is_dir():
                shutil.rmtree(p)
            elif p.is_file():
                p.unlink()
            removed += 1
        except Exception as e:
            print(f"  ⚠ Failed to remove {pretty_path(p)}: {e}")
            errors += 1

    print(f"\n✅ Removed {removed} items", end="")
    if errors:
        print(f" ({errors} errors)")
    else:
        print(" — workspace is clean!")
    print("   Ready to run the pipeline for a new disease.\n")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Reset the RareDiseasePipeline workspace for a new disease."
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="Keep database downloads and disease cache (useful for re-runs)",
    )
    args = parser.parse_args()

    targets = collect_targets(keep_cache=args.keep_cache)
    print_plan(targets)

    if not targets:
        return

    if args.dry_run:
        print("  (Dry run — nothing was deleted)\n")
        return

    if not args.yes:
        answer = input("  Proceed with cleanup? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("  Cancelled.\n")
            return

    execute_cleanup(targets)


if __name__ == "__main__":
    main()
