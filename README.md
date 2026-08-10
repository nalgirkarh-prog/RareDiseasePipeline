# 🧬 RareDiseasePipeline v2

## Automated Genomic Drug Discovery Pipeline for Rare Disease Research

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

RareDiseasePipeline is an automated computational biology workflow that accelerates early-stage rare disease drug discovery by integrating genomic analysis, structural biology, regulatory network mapping, variant annotation, and virtual screening into a single reproducible pipeline.

Given a disease name, the pipeline produces a structured computational report containing ranked drug candidates, docking scores, ADMET properties, variant impact annotations, and simulation-ready system files.

---

# 🚀 Pipeline Overview

## Workflow Architecture

```
Disease Input
      |
      ↓
Stage 00 — Disease Resolver
      |
      ↓
Stage 01 — Gene Identification
      |
      ↓
Stage 02 — Transcript Selection
      |
      ↓
Stage 03 — Protein Mapping
      |
      ↓
Stage 04 — UniProt Mapping
      |
      ↓
Stage 05 — Structure Search (PDB → AlphaFold fallback)
      |
      ↓
Stage 06 — Structure Download + Domain Coverage Check
      |
      ↓
Stage 07 — Regulatory Network Analysis
      |
      ↓
Stage 08 — Binding Pocket Detection (fpocket)
      |          ↳ center/bbox computed from alpha-sphere coordinates
      ↓
Stage 09 — Variant Retrieval (ClinVar esummary)
      |
      ↓
Stage 10 — Variant Impact Analysis (Ensembl VEP)
      |
      ↓
Stage 11 — Ligand Screening (3 sets × 10, ChEMBL)
      |
      ↓
Stage 12 — Molecular Docking (AutoDock Vina)
      |          ↳ per-ligand 120s timeout + crash-recovery checkpoint
      ↓
Stage 13 — Candidate Ranking
      |          ↳ full audit log of all attempts (success / failed / timeout)
      ↓
Stage 14 — Drug-likeness & H-Bond Evaluation
      |
      ↓
Stage 15 — Simulation Builder
      |
      ↓
Stage 16 — Report Generation
```

---

# ✨ Features

## 1. Disease-to-Gene Resolution

Given a rare disease name, the pipeline identifies the associated molecular target through an internal disease-target database.

```
Input:  Rett Syndrome
Output: MECP2
```

---

## 2. Gene Characterization

Retrieves from Ensembl:

- Gene symbol and Ensembl gene ID
- Chromosomal location and strand
- Available transcripts and protein-coding status

---

## 3. Transcript Selection

Selects the canonical protein-coding transcript to eliminate downstream ambiguity during structural and variant analysis.

```
Canonical Transcript: MECP2-201
Transcript ID:        ENST00000303391
```

---

## 4. Protein Characterization

Retrieves:

- Ensembl protein identifier
- UniProt accession
- Amino acid sequence and full-length residue count

```
Protein: MECP2
UniProt: P51608
Length:  498 amino acids
```

---

## 5. Protein Structure Retrieval + Domain Coverage & Remaking Fallback

Searches RCSB PDB for experimentally determined structures. All structures are run through **PDBFixer** (adds missing atoms/residues, replaces non-standard residues).

**Automatic Structure Remaking Fallback (new):** After downloading, the pipeline computes `domain_coverage = chain_residue_count / full_protein_length`. If the experimental PDB structure is broken, corrupted, or incomplete (covering < 50% of the full-length protein, e.g. an isolated domain crystal like MECP2's MBD), the pipeline **automatically remakes the full-length structure using AlphaFold**. This reduces structure-related pipeline failures to near zero.

**AlphaFold disorder check (new):** For AlphaFold models, the mean pLDDT of the TRD region (residues 200–310) is computed from B-factors. A mean pLDDT < 70 triggers an additional warning — preventing false confidence that an AlphaFold download resolves a disordered region.

```
Structure:       AF_P51608 (Remade full-length model)
Domain Coverage: 100% (498/498 aa)
🔄 Note: Experimental structure 1QK9 was incomplete (17% coverage).
         Automatically remade full-length structure using AlphaFold.
```

---

## 6. Regulatory Network Analysis

Identifies molecular partners and regulatory proteins via STRING DB interaction data. Interaction scoring prioritizes biologically relevant regulators.

```
MECP2 regulators: NCOR1 (0.999), SIN3A (0.998), HDAC1 (0.977), HDAC2 (0.975)
```

---

## 7. Binding Pocket Detection

Identifies candidate ligand-binding regions using **fpocket**. Output per pocket:

- Pocket ID, score, volume (Å³), druggability score
- **Center coordinates** (x, y, z) — computed from alpha-sphere atom centroids
- **Bounding box dimensions** (size_x, size_y, size_z) — used directly as the AutoDock Vina search box

> **Previously:** `center_x/y/z` and `size_x/y/z` were always `null` despite fpocket running successfully. Now they are computed from each pocket's `_vert.pqr` file and populated into the `Pocket` model before docking.

```
Pocket:       pocket9
Volume:       500.7 Å³
Druggability: 0.769
Center:       (x=12.4, y=−3.1, z=8.7)
Box:          (18.0 × 14.3 × 16.5 Å)
```

---

## 8. Variant Retrieval (ClinVar esummary)

Fetches ClinVar records for the target gene. Each variant is now annotated with real data from the **ClinVar esummary JSON endpoint**:

- `hgvs_c` — NM_-prefixed coding HGVS (e.g., `NM_004992.4:c.397C>T`)
- `hgvs_p` — Protein HGVS (e.g., `NP_004983.2:p.Arg133Cys`)
- `clinical_significance` — e.g., `Pathogenic`, `Likely pathogenic`, `VUS`
- `residue` — integer extracted from HGVS protein notation

> **Previously:** Every variant was hardcoded to `clinical_significance="unknown"`, `hgvs_c=None`, `hgvs_p=None` — indistinguishable from a stage that never ran. Fields that genuinely have no ClinVar data now return `None` rather than the misleading sentinel.

---

## 9. Variant Impact Analysis (Ensembl VEP)

For each variant with a coding HGVS string, calls the **Ensembl VEP REST API** to retrieve the `most_severe_consequence` (e.g., `missense_variant`, `stop_gained`). Maps each variant to a functional domain (MBD, TRD, CTD, N-terminal) using residue coordinates.

Output per variant:

| Field | Source |
|---|---|
| `hgvs_c` / `hgvs_p` | ClinVar esummary |
| `clinical_significance` | ClinVar esummary |
| `consequence` | Ensembl VEP |
| `region` | Residue → domain map |
| `mapped` | Residue ≤ protein length |

---

## 10. Ligand Screening

Retrieves candidate molecules from **ChEMBL** structured as **3 sequential sets of 10 ligands** (up to 30 total). Each ligand is annotated with:

- Molecular weight, LogP, HBD, HBA, rotatable bonds, SMILES

Docking acts as the primary filter; pre-screening does not eliminate candidates based on ADMET alone.

---

## 11. Molecular Docking — Reliability & Diagnostics

Docking is executed with **AutoDock Vina** using a **pocket-specific search box** derived from fpocket alpha-sphere coordinates.

### Screening Protocol

1. Dock all three sets of 10 sequentially; collect any ligand scoring ≤ −7.0 kcal/mol.
2. Select the single best ligand by most negative affinity (ties broken by reported energy).
3. **Fallback:** if nothing clears −7.0 kcal/mol, select the least-bad negative score across all sets.
4. Non-binding scores (> 0 kcal/mol) are excluded from candidate selection.

### Reliability improvements (new)

**Per-ligand 120-second hard timeout:** Each ligand is docked inside a `ThreadPoolExecutor` with a 120s wall-clock limit. A hung Vina process triggers `status="timeout"` and the loop continues — one stuck ligand can no longer silently kill the whole stage.

**Crash-recovery checkpointing:** `output/docking_checkpoint.json` is written after every ligand attempt. A pipeline restart resumes from the last completed ligand rather than redoing all preceding ones.

**Complete result audit:** Every attempt — whether `success`, `failed`, or `timeout` — is persisted with its status and, on failure, a real error message. Results are written to `output/docking_all_results.json`.

**Parity-check log line:** At the end of docking, a summary is always printed:
```
📊 Docking parity OK — screened=14 attempted=14 success=1 failed/timeout=13
```
Or, if some ligands were not attempted at all:
```
⚠️ PARITY WARNING — screened=14 attempted=11 (delta=3)
```
This pins the ligand-attrition point to the docking stage vs. ranking/report generation — previously undiagnosable from the log alone.

---

## 12. Candidate Ranking

Filters to `status="success"` entries before ranking. Logs how many failed/timeout entries were excluded. Saves:

- `output/docking_ranking.csv` / `.json` — ranked successful candidates
- `output/docking_all_results.json` — full audit log including failures

---

## 13. Drug-likeness & H-Bond Evaluation

Candidates are scored against:

- **Lipinski Rule of Five** (MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10)
- **Veber Filter** (Rotatable bonds ≤ 10, TPSA ≤ 140)
- **Ghose Filter** (160 ≤ MW ≤ 480, −0.4 ≤ LogP ≤ 5.6)
- **Egan Filter** (LogP ≤ 5.88, TPSA ≤ 131)
- **Muegge Filter** (200 ≤ MW ≤ 600, −2 ≤ LogP ≤ 5, TPSA ≤ 150, HBA ≤ 10, HBD ≤ 5, Rot ≤ 15)
- **H-Bond Compliance** (0 ≤ HBD ≤ 5, 0 ≤ HBA ≤ 10, 1 ≤ HBD+HBA ≤ 12) → +10 bonus

**Drug Score** = rule compliance (+15–20 pts each) + QED score (×30) + H-bond bonus (+10) + binding energy bonus (min(−affinity × 3, 30), affinity < 0 only).

---

## 14. Simulation Preparation

Top-ranked candidates are forwarded for molecular dynamics (MD) preparation via GROMACS and AmberTools.

Eligibility logic:
- Affinity ≤ −7.0 kcal/mol → full MD system built.
- Any negative affinity (fallback) → MD system still built.
- Non-binding score (≥ 0) → simulation skipped with a log message.

Output: complete `run_md.sh` script and topology parameters for a 4-step MD simulation.

**Fault-tolerant:** Incompatible crystallographic heteroatoms are automatically stripped. A fragmented structure gracefully skips simulation setup without crashing the report.

---

# 📂 Project Structure

```
RareDiseasePipeline_clean/
│
├── main.py                    # Entry point
├── run_pipeline.py            # Pipeline runner
├── requirements.txt
├── environment.yml
│
├── pipeline/
│   ├── pipeline.py            # Stage orchestrator
│   ├── stage00_resolve.py     # Disease → gene symbol
│   ├── stage01_gene.py        # Gene characterization
│   ├── stage02_transcript.py  # Canonical transcript selection
│   ├── stage03_protein.py     # Protein mapping
│   ├── stage04_uniprot.py     # UniProt accession
│   ├── stage05_structure.py   # PDB search
│   ├── stage06_download.py    # Download + domain coverage check
│   ├── stage07_regulation.py  # Regulatory network
│   ├── stage08_pocket.py      # fpocket detection
│   ├── stage09_variants.py    # ClinVar esummary retrieval
│   ├── stage10_variant_analysis.py  # Ensembl VEP consequence
│   ├── stage11_ligand.py      # ChEMBL ligand screening
│   ├── stage12_docking.py     # Vina docking (timeout + checkpoint)
│   ├── stage13_ranking.py     # Ranking + audit log
│   ├── stage14_drug_evaluation.py
│   ├── stage15_solution_builder.py
│   └── stage16_report.py
│
├── modules/
│   ├── pocket_analysis.py     # fpocket info parser (+ geometry wiring)
│   ├── pocket_geometry.py     # Alpha-sphere centroid + bbox calculator
│   ├── variant_analysis.py    # Residue/domain mapping
│   ├── receptor_preparer.py
│   ├── ligand_preparer.py
│   ├── report_generator.py
│   └── ...
│
├── clients/
│   ├── clinvar.py             # ClinVar (esearch + esummary + efetch)
│   ├── ensembl.py             # Ensembl REST (+ VEP endpoint)
│   ├── vina.py                # AutoDock Vina subprocess wrapper
│   ├── fpocket.py
│   ├── rcsb.py
│   ├── chembl.py
│   └── ...
│
├── models/
│   ├── structure.py           # + domain_coverage, alphafold_trd_plddt
│   ├── pocket.py              # center_x/y/z, size_x/y/z
│   ├── variant.py
│   ├── protein.py             # length field
│   └── ...
│
├── output/
│   ├── docking/               # Per-ligand pose PDBQT + log
│   ├── docking_checkpoint.json      # Crash-recovery checkpoint
│   ├── docking_all_results.json     # Full audit (success/failed/timeout)
│   ├── docking_ranking.csv / .json  # Ranked successful candidates
│   └── reports/
│
├── database/
│   └── structures/
│
└── utils/
    ├── logger.py
    ├── http.py
    └── dependency_checker.py
```

---

# ⚙️ Installation

## Requirements

- Linux environment
- Python 3.12
- Conda

## Clone Repository

```bash
git clone https://github.com/yourusername/RareDiseasePipeline.git
cd RareDiseasePipeline
```

## Create Environment

```bash
conda env create -f environment.yml   # creates the rdpipeline environment
conda activate rdpipeline
```

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Usage

```bash
python main.py
```

```
Enter disease name: Rett Syndrome
```

Example output:

```
==============================================
🏆 FINAL PIPELINE RESULTS 🏆
==============================================
Top Candidate : CHEMBL1650632
Binding Affinity : -8.45 kcal/mol
Overall Drug Score : 107.0
==============================================
```

### Checkpoint / Resume

If docking crashes mid-run, simply re-run the same command. The pipeline detects `output/docking_checkpoint.json` and resumes from the last completed ligand automatically.

---

# 📊 Diagnostic Outputs

| File | Contents |
|---|---|
| `output/docking_checkpoint.json` | Per-ligand state (used for crash recovery) |
| `output/docking_all_results.json` | Every attempt: status, affinity, error message |
| `output/docking_ranking.csv` | Ranked successful candidates |
| `output/docking_ranking.json` | Same, machine-readable |
| `output/reports/` | Full pipeline report |

The **parity-check log line** in Stage 12 and the **domain coverage warning** in Stage 06 are printed to stdout and captured in `pipeline.log`.

---

# 🧪 Validation and Scientific Interpretation

RareDiseasePipeline is a computational prioritization platform. All predictions require independent validation through:

- Literature review and target validation
- Biochemical and biophysical assays
- Cellular and in vivo studies
- Molecular dynamics simulations
- Structural crystallography

The pipeline should be treated as a hypothesis-generation tool, not a replacement for experimental research.

---

# ⚠️ Limitations

- Disease-gene relationships depend on available databases
- Docking scores correlate with, but do not directly predict, biological activity
- Domain-only PDB structures limit pocket detection and docking to the crystallized region
- Intrinsically disordered regions (e.g., MECP2 TRD) cannot be reliably modelled by AlphaFold
- Experimental validation remains essential for all candidates

---

# 🔬 Research Applications

- Rare genetic disorder target analysis
- Computational drug repurposing and repositioning
- Structure-based candidate prioritization
- Variant impact assessment for rare disease mutations
- Molecular simulation preparation
- Bioinformatics education and training

---

# 📜 Citation

If you use RareDiseasePipeline in research, please cite:

```
Harsh Nalgirkar.
RareDiseasePipeline: Automated Genomic Drug Discovery Pipeline for Rare Disease Research.
2026.

@software{nalgirkar2026rarediseasepipeline,
  author    = {Harsh Nalgirkar},
  title     = {RareDiseasePipeline: A Modular Research Software Platform for
               Automated Disease-to-Molecular-Dynamics System Preparation},
  year      = {2026},
  version   = {2.0.0},
  publisher = {GitHub},
  url       = {(https://github.com/nalgirkarh-prog/RareDiseasePipeline)},
  note      = {Accessed: 2026-08-09},
  license   = {MIT}
}
```

---

# 👨‍🔬 Author

**Harsh Nalgirkar**

Department of Pharmacy  
LSHGCT's Gahlot Institute of Pharmacy  
University of Mumbai  
Navi Mumbai, India

Research interests: Computational Drug Discovery · Molecular Dynamics Simulation · Bioinformatics · Rare Disease Therapeutics

---

# 📄 License

MIT License — Copyright (c) 2026 Harsh Nalgirkar

Permission is hereby granted to use, modify, and distribute this software with appropriate attribution.
