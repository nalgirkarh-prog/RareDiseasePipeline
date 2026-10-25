# 🧬 RareDiseasePipeline v3

## Automated Genomic Drug Discovery Pipeline for Rare Disease Research

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)
![Version](https://img.shields.io/badge/Version-3.0.0-purple)

RareDiseasePipeline is an automated computational biology workflow that accelerates early-stage rare disease drug discovery by integrating genomic analysis, structural biology, regulatory network mapping, variant annotation, and virtual screening into a single reproducible pipeline.

Given a disease name or gene symbol, the pipeline produces a structured computational report containing ranked drug candidates, docking scores, ADMET properties, variant impact annotations, and simulation-ready system files.

---

# 🆕 What's New in v3

## Critical Bug Fix: Disease Resolver Mapping

**v2 defect:** When the pipeline received an input like `DMD`, Stage 00 (Disease Resolver) could incorrectly resolve it to `ERBB2` (HER2, Chr 17) instead of `DMD` (Dystrophin, Chr X / HGNC:2928). The root cause was a two-stage NCBI E-utilities fallback: the `[Disease/Phenotype]` field returned zero hits for acronyms, so the fallback used `[All Fields]`, where ERBB2 ranked first by relevance. The incorrect mapping was then **cached**, poisoning every subsequent re-run.

**v3 fixes:**

- **Option B — Curated HGNC Symbol Map (100+ Rare Diseases):** `DiseaseResolverEngine` now checks an extensive `KNOWN_DISEASE_MAP` before hitting external APIs. This covers over 100 rare diseases across 12 distinct therapeutic areas:
  - *Muscular Dystrophies:* DMD, BMD, LGMD (CAPN3), FSHD (DUX4)
  - *Neurological:* Rett (MECP2), SMA (SMN1), Huntington (HTT), Fragile X (FMR1), ALS (SOD1), Friedreich Ataxia (FXN), CMT (PMP22), SCA1 (ATXN1), Myotonic Dystrophy (DMPK), Parkinson (SNCA), Alzheimer (APP), Angelman (UBE3A), Prader-Willi (SNRPN), Dravet (SCN1A)
  - *Lysosomal Storage Disorders:* Gaucher (GBA1), Fabry (GLA), Tay-Sachs (HEXA), Pompe (GAA), Niemann-Pick (SMPD1/NPC1), Krabbe (GALC), MLD (ARSA), MPS I/Hurler (IDUA), MPS II/Hunter (IDS)
  - *Hematology:* Sickle Cell Disease (HBB), Thalassemia alpha/beta (HBA1/HBB), Hemophilia A/B (F8/F9), von Willebrand (VWF), Fanconi Anemia (FANCA)
  - *Connective Tissue & Bone:* Marfan (FBN1), Ehlers-Danlos (COL5A1), Osteogenesis Imperfecta (COL1A1), Stickler (COL2A1), Achondroplasia (FGFR3)
  - *Immunology:* SCID (IL2RG), XLA (BTK), Wiskott-Aldrich (WAS), DiGeorge (TBX1)
  - *Metabolic:* PKU (PAH), Wilson (ATP7B), MSUD (BCKDHA), Galactosemia (GALT), Homocystinuria (CBS), MCADD (ACADM), GSD1 (G6PC1), Biotinidase (BTD), Propionic Acidemia (PCCA)
  - *Cardiology:* LQTS (KCNQ1), HCM (MYH7), DCM (LMNA), Brugada (SCN5A), ARVC (PKP2), CPVT (RYR2)
  - *Pulmonology:* Cystic Fibrosis (CFTR), Alpha-1 Antitrypsin (SERPINA1), Primary Ciliary Dyskinesia (DNAI1)
  - *Nephrology:* ADPKD (PKD1), Alport (COL4A5)
  - *Ophthalmology:* Retinitis Pigmentosa (RHO), Leber Congenital Amaurosis (RPE65), Stargardt (ABCA4)
  - *Cancer & Syndromes:* NF1, NF2, Li-Fraumeni (TP53), FAP (APC), VHL, Tuberous Sclerosis (TSC1), Retinoblastoma (RB1), Williams (ELN), Noonan (PTPN11), Alagille (JAG1), Kabuki (KMT2D), CdLS (NIPBL), Progeria (LMNA)
- **Option A — Direct Gene Symbol Bypass:** If a `gene_symbol` is passed on the `Disease` model or via the CLI (`--gene DMD`), Stage 00 skips all resolver logic and uses the explicit symbol immediately.
- **Cache Purge & Stale Cache Protection:** The poisoned `{"dmd": "ERBB2"}` entry is detected and removed at runtime. The cache is pre-seeded with correct entries for all curated diseases.
- **NCBI Query Priority Fix:** `NCBIGeneClient` now queries `[Gene Name]` first for gene-symbol-shaped inputs (2–10 uppercase alphanumeric chars), then `[Disease/Phenotype]`, then `[Gene/Protein Name]` — eliminating the `[All Fields]` relevance collisions that caused the mismatch.

## Advanced Scientific Improvements

### 1. ClinVar Pathogenic Variant Prioritization
- **Two-tier query system:** `ClinVarClient` queries for explicit `("pathogenic"[clinical_significance] OR "likely pathogenic"[clinical_significance])` records first, followed by broader gene variants (up to 500 records searched).
- **Expanded capacity:** Variant retrieval capacity expanded to 50 deduplicated, pathogenic-prioritized alleles per target gene.
- **Structural variant identification:** Detects and parses `variation_type` (deletions, duplications, frameshifts, single nucleotide variants).

### 2. Primary Target Screening in ChEMBL
- `LigandDiscovery` now queries the **primary gene target directly in ChEMBL** first to harvest verified active compounds for the target protein before querying secondary STRING partners.
- Global screening cap expanded from 30 to 50 candidate molecules across sequential sets.

### 3. Mutation-Guided Pocket Selection & Safety Gates
- **Druggability gating:** Enforces a `MIN_DRUGGABILITY = 0.2` threshold to filter out geometrically artifactual or non-druggable pockets.
- **Residue-overlap mapping:** Pocket-lining residues are parsed from fpocket atom PDB files and mapped against known ClinVar pathogenic variant residues. Pockets that directly overlap or contact disease-causing mutations are **automatically prioritized** for molecular docking.
- **Centroid validation:** Prevents unconstrained whole-protein docking by asserting valid bounding boxes before Vina execution.

### 4. PDBFixer Caching
- Stage 06 caches `_fixed.pdb` structures, eliminating redundant 2-minute fixing cycles on repeat pipeline runs.

## CLI Enhancements

New flags added to `main.py`:

```bash
# Option A: bypass resolver — pass explicit HGNC gene symbol
python main.py "DMD" --gene DMD

# Stop after Stage 10 (variant analysis), skip interactive prompts
python main.py "Duchenne muscular dystrophy" --max-stage 10 --non-interactive

# Full interactive pipeline (default, unchanged)
python main.py
```

| Flag | Short | Description |
|---|---|---|
| `--gene SYMBOL` | `-g` | Explicit HGNC gene symbol; bypasses Stage 00 resolver entirely |
| `--max-stage N` | `-s` | Stop after Stage N (0–16); no interactive depth prompt required |
| `--non-interactive` | `-y` | Disable all Human-in-the-Loop prompts for automated runs |

## Stage 03 — Protein Model

`protein.transcript_id` is now populated from the canonical transcript selected in Stage 02. This is forwarded to Stage 10 so the Ensembl VEP call uses the correct transcript (`ENST…`) rather than the ClinVar accession as a fallback.

## Stage 10 — Variant Analysis Upgrades

- **Canonical transcript routing to VEP:** `ENST00000357033` (or whichever transcript was selected) is passed to the VEP endpoint, ensuring consequences are resolved against the right isoform.
- **Gene-aware functional domain mapping:** `VariantAnalyzer.predict_region()` now accepts `gene_symbol` and applies protein-specific domain boundaries:

  **DMD — Dystrophin** (3,685 aa):
  | Residues | Domain |
  |---|---|
  | 1 – 240 | Actin-Binding Domain 1 (ABD1 / Calponin-Homology) |
  | 241 – 3,040 | Central Rod Domain (Spectrin Repeats R1–R24 + Hinges) |
  | 3,041 – 3,408 | Cysteine-Rich Domain (CRD / β-Dystroglycan Binding) |
  | 3,409 – 3,685 | C-Terminal Domain (CTD / Syntrophin-Dystrobrevin Binding) |

  **MECP2** and all other proteins retain the existing MBD / TRD / CTD boundaries as the default fallback.

## Validated on DMD — Stages 00 to 10

The full corrected run for `DMD` produced:

| Stage | Output |
|---|---|
| **00** Disease Resolver | `DMD → DMD` via curated HGNC map (HGNC:2928, Dystrophin, Chr X Xp21.2-p21.1) |
| **01** Gene Fetcher | `ENSG00000198947`, Chr X, 31,097,677–33,339,609 bp (~2.24 Mb) |
| **02** Transcript | `ENST00000357033` (DMD-203, canonical, 79 exons) |
| **03** Protein | `ENSP00000354923`, 3,685 aa |
| **04** UniProt | `P11532` (DMD_HUMAN, Dystrophin) |
| **05** Structure Search | `1DXX` (ABD1 crystal, Chr X Xp21) |
| **06** Structure Download | 1DXX domain coverage = 7% → auto-fallback to `AF_P11532` (full-length AlphaFold) |
| **07** Regulatory Analysis | 52 STRING interactions: `SNTB1`, `SGCD`, `SGCA`, `CTNNAL1`, `SNTB2` |
| **08** Pocket Detection | 54 fpocket binding pockets detected |
| **09** ClinVar Variants | 10 variants retrieved (7 with protein HGVS) |
| **10** VEP Consequences | `stop_gained` · `missense_variant` · `splice_acceptor_variant` — all correctly attributed to Dystrophin |

ClinVar variants correctly resolved for Dystrophin (not ERBB2):

| ClinVar UID | HGVS Coding | HGVS Protein | Significance | VEP | Domain |
|---|---|---|---|---|---|
| 5011354 | `c.5425G>T` | `p.Glu1809Ter` | **Pathogenic** | `stop_gained` | Central Rod Domain |
| 5020078 | — | — | **Pathogenic** | — | Structural Deletion |
| 5008800 | `c.149T>C` | `p.Leu50Pro` | VUS | `missense_variant` | ABD1 (Actin-Binding) |
| 5019832 | `c.9690C>G` | `p.Asp3230Glu` | VUS | `missense_variant` | CRD (β-Dystroglycan) |
| 5018219 | `c.9665T>C` | `p.Val3222Ala` | VUS | `missense_variant` | CRD (β-Dystroglycan) |
| 5004733 | `c.2191_2193delinsGTA` | `p.Leu731Val` | VUS | `missense_variant` | Central Rod Domain |
| 5004664 | `c.2096C>T` | `p.Ala699Val` | VUS | `missense_variant` | Central Rod Domain |
| 5004802 | `c.9810TAA` | `p.Asn3272del` | VUS | In-frame Deletion | CRD (β-Dystroglycan) |
| 5004527 | `c.10224-1G>T` | — | VUS | `splice_acceptor_variant` | Canonical Splice Site |

---

# 🚀 Pipeline Overview

## Workflow Architecture

```
Disease Input  (name, acronym, or --gene SYMBOL)
      |
      ↓
Stage 00 — Disease Resolver
           ├─ Curated HGNC map (fast, offline)
           ├─ Explicit gene_symbol bypass
           └─ NCBI Gene E-utilities fallback
      |
      ↓
Stage 01 — Gene Identification (Ensembl)
      |
      ↓
Stage 02 — Transcript Selection (canonical)
      |
      ↓
Stage 03 — Protein Mapping  [+ transcript_id propagation]
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
Stage 07 — Regulatory Network Analysis (STRING)
      |
      ↓
Stage 08 — Binding Pocket Detection (fpocket)
      |          ↳ center/bbox computed from alpha-sphere coordinates
      ↓
Stage 09 — Variant Retrieval (ClinVar esummary)
      |
      ↓
Stage 10 — Variant Impact Analysis (Ensembl VEP)  [+ gene-aware domain mapping]
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

# ✨ Features & Human-in-the-Loop Interactivity

## 0. Human-in-the-Loop Research Controls

RareDiseasePipeline is designed as an interactive research software platform that empowers researchers to guide, override, and customize pipeline decisions:

- **Selective Pipeline Execution Depth:** At startup, researchers can choose how far the pipeline runs — from lightweight preliminary target mapping (Stage 04) or pocket detection (Stage 08) up to full-scale molecular docking and simulation setup (Stage 16). Or use `--max-stage N` to set this non-interactively.
- **Protein Structure Override:** Before downloading or docking, the user can inspect the pipeline's selected structure and override it with a literature PDB ID (e.g. `2ARF`) or a custom local `.pdb` file path from their own experimental research.
- **Literature Ligand Input & Substitution:** After automated ChEMBL screening, researchers can enter SMILES strings, PubChem CIDs, or ChEMBL IDs for candidates identified in literature. These user-supplied ligands are automatically calculated via RDKit and included in the docking screen.

---

## 1. Disease-to-Gene Resolution

Given a rare disease name or acronym, the pipeline resolves the primary molecular target through a three-tier system:

1. **Curated HGNC Map** — instant, offline, no API calls
2. **Explicit bypass** (`--gene SYMBOL` or `Disease(gene_symbol=...)`)
3. **NCBI Gene E-utilities** — with improved query priority to prevent false-positive matches

```
Input:  DMD
Output: DMD  (HGNC:2928, Dystrophin, Chr X)

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
Canonical Transcript: ENST00000357033  (DMD-203)
```

---

## 4. Protein Characterization

Retrieves:

- Ensembl protein identifier
- Canonical transcript ID (propagated to Stage 10 for VEP)
- UniProt accession
- Amino acid sequence and full-length residue count

```
Protein:     ENSP00000354923  (Dystrophin)
UniProt:     P11532
Length:      3,685 amino acids
Transcript:  ENST00000357033
```

---

## 5. Protein Structure Retrieval + Domain Coverage & Remaking Fallback

Searches RCSB PDB for experimentally determined structures. All structures are run through **PDBFixer** (adds missing atoms/residues, replaces non-standard residues).

**Automatic Structure Remaking Fallback:** After downloading, the pipeline computes `domain_coverage = unique_residue_count / full_protein_length`. If the experimental PDB structure is broken, corrupted, or incomplete (covering < 50% of the full-length protein, e.g. a domain-only crystal), the pipeline **automatically remakes the full-length structure using AlphaFold**. This reduces structure-related pipeline failures to near zero.

**AlphaFold disorder check:** For AlphaFold models, the mean pLDDT of the TRD region (residues 200–310) is computed from B-factors. A mean pLDDT < 70 triggers an additional warning — preventing false confidence that an AlphaFold download resolves a disordered region.

```
Structure:       AF_P11532 (AlphaFold fallback, full-length Dystrophin)
Original PDB:    1DXX (ABD1 crystal, 7% domain coverage)
Note:  Experimental structure 1DXX was incomplete (7% coverage).
       Automatically remade full-length structure using AlphaFold.
```

---

## 6. Regulatory Network Analysis

Identifies molecular partners and regulatory proteins via STRING DB interaction data. Interaction scoring prioritizes biologically relevant regulators.

```
DMD regulators: SNTB1, SGCD, SGCA, CTNNAL1, SNTB2 (52 total interactions)
```

---

## 7. Binding Pocket Detection

Identifies candidate ligand-binding regions using **fpocket**. Output per pocket:

- Pocket ID, score, volume (Å³), druggability score
- **Center coordinates** (x, y, z) — computed from alpha-sphere atom centroids
- **Bounding box dimensions** (size_x, size_y, size_z) — used directly as the AutoDock Vina search box

```
Pocket:       pocket1
Volume:       500.7 Å³
Druggability: 0.769
Center:       (x=12.4, y=−3.1, z=8.7)
Box:          (18.0 × 14.3 × 16.5 Å)
```

---

## 8. Variant Retrieval (ClinVar esummary)

Fetches ClinVar records for the target gene. Each variant is annotated with real data from the **ClinVar esummary JSON endpoint**:

- `hgvs_c` — NM_-prefixed coding HGVS (e.g., `NM_004006.3:c.5425G>T`)
- `hgvs_p` — Protein HGVS (e.g., `p.Glu1809Ter`)
- `clinical_significance` — e.g., `Pathogenic`, `Likely pathogenic`, `VUS`
- `residue` — integer extracted from HGVS protein notation

---

## 9. Variant Impact Analysis (Ensembl VEP)

For each variant with a coding HGVS string, calls the **Ensembl VEP REST API** using the canonical transcript ID to retrieve the `most_severe_consequence` (e.g., `missense_variant`, `stop_gained`, `splice_acceptor_variant`). Maps each variant to a functional domain using **gene-specific residue boundary definitions**.

Output per variant:

| Field | Source |
|---|---|
| `hgvs_c` / `hgvs_p` | ClinVar esummary |
| `clinical_significance` | ClinVar esummary |
| `consequence` | Ensembl VEP (via canonical transcript) |
| `region` | Residue → gene-aware domain map |
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

### Reliability Improvements

**Per-ligand 120-second hard timeout:** Each ligand is docked inside a `ThreadPoolExecutor` with a 120s wall-clock limit. A hung Vina process triggers `status="timeout"` and the loop continues.

**Crash-recovery checkpointing:** `output/docking_checkpoint.json` is written after every ligand attempt. A pipeline restart resumes from the last completed ligand.

**Complete result audit:** Every attempt — whether `success`, `failed`, or `timeout` — is persisted with its status and error message. Results are written to `output/docking_all_results.json`.

**Parity-check log line:**
```
📊 Docking parity OK — screened=14 attempted=14 success=1 failed/timeout=13
```

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
RareDiseasePipeline/
│
├── main.py                    # Entry point  [v3: --gene, --max-stage, --non-interactive]
├── run_pipeline.py            # Pipeline runner
├── requirements.txt
├── environment.yml
│
├── pipeline/
│   ├── pipeline.py            # Stage orchestrator  [v3: max_stage param]
│   ├── stage00_resolve.py     # Disease → gene symbol  [v3: explicit bypass]
│   ├── stage01_gene.py        # Gene characterization
│   ├── stage02_transcript.py  # Canonical transcript selection
│   ├── stage03_protein.py     # Protein mapping  [v3: transcript_id propagation]
│   ├── stage04_uniprot.py     # UniProt accession
│   ├── stage05_structure.py   # PDB search
│   ├── stage06_download.py    # Download + domain coverage check
│   ├── stage07_regulation.py  # Regulatory network
│   ├── stage08_pocket.py      # fpocket detection
│   ├── stage09_variants.py    # ClinVar esummary retrieval
│   ├── stage10_variant_analysis.py  # Ensembl VEP  [v3: transcript routing]
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
│   ├── variant_analysis.py    # Residue/domain mapping  [v3: gene-aware domains]
│   ├── receptor_preparer.py
│   ├── ligand_preparer.py
│   ├── report_generator.py
│   └── ...
│
├── clients/
│   ├── disease/
│   │   ├── resolver.py        # [v3: KNOWN_DISEASE_MAP, stale-cache purge, bypass]
│   │   └── cache.py
│   ├── ncbi_client.py         # [v3: [Gene Name] priority fix]
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
│   ├── protein.py             # [v3: transcript_id field]
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
git clone https://github.com/nalgirkarh-prog/RareDiseasePipeline.git
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

### Interactive (default)

```bash
python main.py
```

```
Enter disease name: Rett Syndrome
```

### Command-line disease name

```bash
python main.py "Duchenne muscular dystrophy"
```

### Bypass resolver with explicit gene symbol

```bash
python main.py "DMD" --gene DMD
```

### Run up to Stage 10 only, non-interactively

```bash
python main.py "DMD" --max-stage 10 --non-interactive
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

- Disease-gene relationships depend on available databases; curated maps cover the most common rare diseases only
- Docking scores correlate with, but do not directly predict, biological activity
- Domain-only PDB structures limit pocket detection and docking to the crystallized region
- Intrinsically disordered regions (e.g., MECP2 TRD, large central rod segments of Dystrophin) cannot be reliably modelled by AlphaFold
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
  version   = {3.0.0},
  publisher = {GitHub},
  url       = {https://github.com/nalgirkarh-prog/RareDiseasePipeline},
  note      = {Accessed: 2026-10-25},
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
