# 🧬 RareDiseasePipeline

## Automated Genomic Drug Discovery Pipeline for Rare Disease Research

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

RareDiseasePipeline is an automated computational biology workflow designed to accelerate early-stage rare disease drug discovery by integrating genomic analysis, transcript selection, protein characterization, structural biology, regulatory network analysis, binding pocket detection, and virtual screening.

The pipeline converts a disease name into a structured computational report containing:

- Disease-associated gene identification
- Transcript and protein characterization
- Protein structure acquisition
- Regulatory interaction analysis
- Binding pocket prediction
- Variant annotation framework
- Ligand retrieval and drug-likeness evaluation
- Molecular docking-based prioritization
- Simulation-ready ligand selection

The objective of RareDiseasePipeline is not to replace experimental validation, but to provide researchers with a reproducible computational framework for hypothesis generation and candidate prioritization.

---

# 🚀 Pipeline Overview

## Workflow Architecture

```
Disease Input
      |
      ↓
Disease Resolver
      |
      ↓
Gene Identification
      |
      ↓
Transcript Selection
      |
      ↓
Protein Mapping
      |
      ↓
Structure Retrieval
      |
      ↓
Regulatory Analysis
      |
      ↓
Binding Pocket Detection
      |
      ↓
Variant Analysis
      |
      ↓
Ligand Screening (3 Sets of 10)
      |
      ↓
Molecular Docking (First Filter: ≤ -7.0 kcal/mol)
      |
      ↓
Candidate Ranking
      |
      ↓
Drug-likeness & H-Bond Evaluation
      |
      ↓
Simulation Preparation (Threshold Check ≤ -7.0 kcal/mol)
```

---

# ✨ Features

## 1. Disease-to-Gene Resolution

Given a rare disease name, the pipeline identifies associated molecular targets.

Example:

```
Input:
Wilson Disease

Output:
Gene:
ATP7B
```

Supported diseases are currently maintained through an internal disease-target database.

---

## 2. Gene Characterization

The pipeline retrieves:

- Gene symbol
- Ensembl gene identifier
- Chromosomal location
- Strand information
- Available transcripts
- Protein-coding status

Example:

```
Disease:
Wilson Disease

Target:
ATP7B

Ensembl ID:
ENSG00000123191

Chromosome:
13
```

---

# 3. Transcript Selection

Multiple transcripts may exist for a gene.

RareDiseasePipeline selects the canonical protein-coding transcript where available.

Example:

```
Canonical Transcript:

ATP7B-201

Transcript ID:

ENST00000242839
```

This reduces downstream ambiguity during structural analysis.

---

# 4. Protein Characterization

Protein information is retrieved including:

- Ensembl protein identifier
- UniProt accession
- Amino acid sequence
- Protein length

Example:

```
Protein:

ATP7B

UniProt:

P35670

Length:

1465 amino acids
```

---

# 5. Protein Structure Retrieval

The pipeline automatically retrieves experimentally available protein structures from RCSB PDB.

If experimental structures are unavailable, it will **automatically fall back to AlphaFold** to download a predicted structural model. All downloaded structures (both PDB and AlphaFold) are then automatically run through **PDBFixer** to add missing atoms/residues and replace non-standard residues.

Example:

```
Structure:

PDB ID:
2ARF

File:
database/structures/2ARF.pdb
```

---

# 6. Regulatory Network Analysis

The pipeline identifies associated regulatory proteins and molecular partners.

Example output:

```
ATOX1
CCS
ATP7A
COMMD1
SLC31A1
```

Interaction scoring helps prioritize biologically relevant regulators.

---

# 7. Binding Pocket Detection

Potential ligand-binding regions are identified from the protein structure.

Output includes:

- Pocket ID
- Pocket score
- Volume
- Druggability score

Example:

```
Pocket:

pocket9

Volume:

500.746 Å³

Druggability:

0.769
```

Higher druggability scores indicate potentially more favorable regions for ligand binding.

---

# 8. Variant Analysis

The framework supports disease-associated variant mapping.

Current functionality:

- Variant retrieval
- Variant metadata storage
- Structural mapping framework

Future versions will expand:

- Amino acid substitution mapping
- Stability prediction
- Pathogenicity scoring
- Variant impact analysis

---

# 9. Ligand Screening (3 Sets of 10)

Candidate molecules are retrieved from ChEMBL and structured into **3 sets of 10 ligands** (up to 30 total).

All candidate ligands are prepared without premature pre-filtering, allowing **molecular docking to act as the primary filter**.

Each ligand is annotated with:

- Molecular weight
- LogP
- Hydrogen bond donors (HBD)
- Hydrogen bond acceptors (HBA)
- Rotatable bonds

Example:

```
Ligand:

CHEMBL1650632

MW:

227.29

LogP:

3.67
```

---

# 10. Molecular Docking (First Filter & Sequential 3-Set Protocol)

Molecular docking is executed as the **first filter** using AutoDock Vina.

### Revised 3-Set Screening Protocol:

1. **Dock all three sets (10 ligands each)** sequentially, collecting any ligands with docking affinity ≤ -7.0 kcal/mol.
2. After all sets are processed, **select the single best ligand** based on the most negative affinity (strongest binding). If multiple ligands share the same affinity, the one with the lowest reported energy is chosen.
3. **Fallback Mechanism**: If no ligand meets the ≤ -7.0 kcal/mol threshold, the ligand with the overall lowest (most negative) docking score across all three sets is selected.
4. Positive docking scores (>0) are considered non‑binding and are excluded from candidate selection.

> **Note**: Positive docking scores ($>0$) represent non-binding/repulsive energies and are strictly eliminated from valid candidate selection.

Docking output includes:

- Binding affinity ($\text{kcal/mol}$)
- Docking pose PDBQT
- Detailed execution log

Example:

```
Ligand:

CHEMBL1650632

Affinity:

-8.45 kcal/mol
```

---

# 11. Drug-likeness & H-Bond Evaluation

Candidates passing the docking filter are evaluated against medicinal chemistry rules:

- **Lipinski Rule of Five** (MW $\le 500$, LogP $\le 5$, HBD $\le 5$, HBA $\le 10$)
- **Veber Filter** (Rotatable bonds $\le 10$, TPSA $\le 140$)
- **Ghose Filter** ($160 \le \text{MW} \le 480$, $-0.4 \le \text{LogP} \le 5.6$)
- **Egan Filter** ($\text{LogP} \le 5.88$, TPSA $\le 131$)
- **Muegge Filter** ($200 \le \text{MW} \le 600$, $-2 \le \text{LogP} \le 5$, TPSA $\le 150$, HBA $\le 10$, HBD $\le 5$, Rot $\le 15$)
- **Hydrogen Bond (H-Bond) Factors**: Evaluates balanced H-bonding capacity ($0 \le \text{HBD} \le 5$, $0 \le \text{HBA} \le 10$, $1 \le \text{HBD+HBA} \le 12$) and awards $+10$ bonus points.

Overall **Drug Score** combines rule compliance (+15 to +20 points each), QED score ($\times 30$), H-bond compliance (+10 points), and negative binding energy bonus ($\min(-\text{affinity} \times 3, 30)$ only when $\text{affinity} < 0$).

---

# 12. Simulation Preparation

Top-ranked candidates are forwarded for molecular dynamics (MD) simulation system preparation.

The pipeline applies the following logic for simulation eligibility:

- **If any candidate has a docking score $\le -7.0$ kcal/mol**: that candidate is used and the full MD simulation system is built.
- **If no candidate reaches $\le -7.0$ kcal/mol but all scores are negative** (fallback): the candidate with the highest negative docking score (most negative value, e.g. $-5.2$ over $-3.1$) is selected and the MD simulation system is still built.
- **If the top candidate has a non-binding score ($\ge 0$ kcal/mol)**: simulation setup is skipped entirely with a clear log message.

When a simulation-eligible candidate is identified, the pipeline automatically generates a complete execution script (`run_md.sh`) and topology parameters for a 4-step MD simulation via GROMACS and AmberTools.

**Fault-Tolerant Setup:** The pipeline automatically strips incompatible crystallographic heteroatoms that cause chain-type consistency failures. If a fragmented or biologically incompatible structure is detected, it gracefully skips simulation setup and generates the final research report without crashing.

Example:

```
Protein:

ENSP00000242839

Ligand:

CHEMBL1650632

Affinity:

-8.45 kcal/mol

Simulation Directory:

simulations
```

---

# 📂 Project Structure

```
RareDiseasePipeline/

│
├── main.py
├── requirements.txt
├── README.md
│
├── stages/
│   ├── stage00_resolve/
│   ├── stage01_gene/
│   ├── stage02_transcript/
│   ├── stage03_protein/
│   ├── stage04_uniprot/
│   ├── stage05_structure/
│   ├── stage06_download/
│   ├── stage07_regulation/
│   ├── stage08_pocket/
│
├── database/
│   └── structures/
│
├── output/
│   ├── docking/
│   └── reports/
│
├── simulations/
│   └── run_md.sh
│
└── reports/
```

---

# ⚙️ Installation

## Requirements

Recommended:

- Linux environment
- Python 3.12
- Conda environment

---

## Clone Repository

```bash
git clone https://github.com/nalgirkarh-prog/RareDiseasePipeline.git

cd RareDiseasePipeline
```

---

## Create Environment

```bash
conda create -n raredrug python=3.10

conda activate raredrug
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Usage

Run:

```bash
python main.py
```

Enter disease name:

Example:

```
Enter disease name:

Wilson Disease
```

Pipeline execution:

```
Resolving disease...
Fetching gene...
Fetching transcript...
Fetching protein...
Mapping UniProt...
Finding structure...
Downloading structure...
Regulatory analysis...
Detecting binding pockets...
Retrieving ligands...
Docking candidates...
Generating report...

==============================================
🏆 FINAL PIPELINE RESULTS 🏆
==============================================
Top Candidate : CHEMBL1650632
Binding Affinity : -8.45 kcal/mol
Overall Drug Score : 107.0
==============================================

---

# 📊 Example Output

Generated reports contain:

```

Disease
 |
Gene
 |
Transcript
 |
Protein
 |
Structure
 |
Binding pockets
 |
Variants
 |
Ligands
 |
Docking scores
 |
Simulation candidates

```
---

# 🧪 Validation and Scientific Interpretation

RareDiseasePipeline is designed as a computational prioritization platform.

All predictions require independent validation through:

- Literature review
- Experimental assays
- Biochemical validation
- Structural analysis
- Molecular dynamics simulations
- Cellular studies

The pipeline should be considered a hypothesis-generation tool rather than a replacement for experimental research.

---

# 🔬 Research Applications

Potential applications include:

- Rare genetic disorder target analysis
- Computational drug repurposing
- Candidate ligand prioritization
- Structure-based drug discovery
- Molecular simulation preparation
- Bioinformatics education and training

---

# 🛣️ Future Development

Planned improvements:

## AI-Assisted Ranking

Integration of:

- ClinVar interpretation
- Variant consequence prediction
- Stability prediction tools

## Enhanced Molecular Simulation

Automated:

- System preparation
- MD setup
- Trajectory analysis
- Binding free energy calculations

## AI-Assisted Ranking

Integration of:

- Machine learning scoring
- ADMET prediction
- Multi-objective optimization

---

# ⚠️ Limitations

Current limitations:

- Disease-gene relationships depend on available databases
- Docking scores do not directly represent biological activity
- Structural availability may limit analysis
- Variant interpretation requires additional annotation
- Experimental validation remains essential

---

# 📜 Citation

If you use RareDiseasePipeline in research, please cite:

```

Harsh Nalgirkar.
RareDiseasePipeline: Automated Genomic Drug Discovery Pipeline for Rare Disease Research.
2026.



@software{nalgirkar2026rarediseasepipeline,
  author       = {Harsh Nalgirkar},
  title        = {RareDiseasePipeline: A Modular Research Software Platform for Automated Disease-to-Molecular-Dynamics System Preparation},
  year         = {2026},
  version      = {1.0.0},
  publisher    = {GitHub},
  url          = {https://github.com/nalgirkarh-prog/RareDiseasePipeline},
  note         = {Accessed: 2026-08-02},
  license      = {MIT}
}


```
---

# 👨‍🔬 Author

**Harsh Nalgirkar**

Department of Pharmacy  
LSHGCT's Gahlot Institute of Pharmacy  
University of Mumbai  
Navi Mumbai, India

Research interests:

- Computational Drug Discovery
- Molecular Dynamics Simulation
- Bioinformatics
- Rare Disease Therapeutics

---

# 📄 License

MIT License

Copyright (c) 2026 Harsh Nalgirkar

Permission is hereby granted to use, modify, and distribute this software with appropriate attribution.

```
