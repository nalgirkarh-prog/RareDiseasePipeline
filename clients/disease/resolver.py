"""
clients/disease/resolver.py

Turns a disease (name / Disease object) into a gene symbol, with a JSON cache
in front of the NCBI call so repeat runs are instant and offline-friendly.

Features:
- Option A (Direct Gene Bypass): If disease has `gene_symbol` specified, returns it directly.
- Option B (Curated HGNC Map): Direct mapping for common disease names and acronyms
  (e.g. DMD -> DMD / HGNC:2928, MECP2, CFTR, etc.) preventing unhandled NCBI string matches.
- JSON cache for fast offline resolution with corrupted-cache protection.
- NCBI Gene E-utilities fallback with clean error handling.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .cache import DiseaseCache
from clients.ncbi_client import NCBIGeneClient
from utils.http import HTTPError


# Curated mapping of common rare diseases, syndromes, and acronyms to HGNC symbols.
KNOWN_DISEASE_MAP = {
    # Muscular dystrophies (DMD / HGNC:2928)
    "dmd": "DMD",
    "duchenne": "DMD",
    "duchenne muscular dystrophy": "DMD",
    "becker muscular dystrophy": "DMD",
    "bmd": "DMD",
    "dystrophin": "DMD",
    "limb-girdle muscular dystrophy": "CAPN3",
    "lgmd": "CAPN3",
    "facioscapulohumeral muscular dystrophy": "DUX4",
    "fshd": "DUX4",

    # Neurological & Neurodevelopmental
    "rett syndrome": "MECP2",
    "rett": "MECP2",
    "rtt": "MECP2",
    "spinal muscular atrophy": "SMN1",
    "sma": "SMN1",
    "huntington's disease": "HTT",
    "huntington disease": "HTT",
    "huntington": "HTT",
    "hd": "HTT",
    "fragile x syndrome": "FMR1",
    "fragile x": "FMR1",
    "fxs": "FMR1",
    "amyotrophic lateral sclerosis": "SOD1",
    "als": "SOD1",
    "friedreich ataxia": "FXN",
    "friedreich's ataxia": "FXN",
    "fa": "FXN",
    "charcot-marie-tooth": "PMP22",
    "charcot-marie-tooth disease": "PMP22",
    "cmt": "PMP22",
    "spinocerebellar ataxia": "ATXN1",
    "spinocerebellar ataxia type 1": "ATXN1",
    "sca": "ATXN1",
    "sca1": "ATXN1",
    "myotonic dystrophy": "DMPK",
    "myotonic dystrophy type 1": "DMPK",
    "dm1": "DMPK",
    "parkinson's disease": "SNCA",
    "parkinson disease": "SNCA",
    "parkinson": "SNCA",
    "alzheimer's disease": "APP",
    "alzheimer disease": "APP",
    "angelman syndrome": "UBE3A",
    "angelman": "UBE3A",
    "prader-willi syndrome": "SNRPN",
    "prader willi": "SNRPN",
    "pws": "SNRPN",
    "early infantile epileptic encephalopathy": "SCN1A",
    "dravet syndrome": "SCN1A",
    "dravet": "SCN1A",

    # Lysosomal Storage Disorders
    "gaucher disease": "GBA1",
    "gaucher": "GBA1",
    "fabry disease": "GLA",
    "fabry": "GLA",
    "tay-sachs disease": "HEXA",
    "tay sachs": "HEXA",
    "pompe disease": "GAA",
    "pompe": "GAA",
    "niemann-pick disease": "SMPD1",
    "niemann-pick disease type a": "SMPD1",
    "niemann-pick disease type b": "SMPD1",
    "niemann-pick disease type c": "NPC1",
    "niemann pick": "NPC1",
    "npc": "NPC1",
    "krabbe disease": "GALC",
    "krabbe": "GALC",
    "metachromatic leukodystrophy": "ARSA",
    "mld": "ARSA",
    "mucopolysaccharidosis type i": "IDUA",
    "mucopolysaccharidosis i": "IDUA",
    "mps1": "IDUA",
    "mps i": "IDUA",
    "hurler syndrome": "IDUA",
    "hurler": "IDUA",
    "mucopolysaccharidosis type ii": "IDS",
    "mucopolysaccharidosis ii": "IDS",
    "mps2": "IDS",
    "mps ii": "IDS",
    "hunter syndrome": "IDS",
    "hunter": "IDS",

    # Hemoglobinopathies & Hematologic Disorders
    "sickle cell disease": "HBB",
    "sickle cell anemia": "HBB",
    "sickle cell": "HBB",
    "scd": "HBB",
    "beta thalassemia": "HBB",
    "beta-thalassemia": "HBB",
    "alpha thalassemia": "HBA1",
    "alpha-thalassemia": "HBA1",
    "hemophilia a": "F8",
    "haemophilia a": "F8",
    "hemophilia b": "F9",
    "haemophilia b": "F9",
    "von willebrand disease": "VWF",
    "von willebrand": "VWF",
    "vwd": "VWF",
    "fanconi anemia": "FANCA",
    "fanconi": "FANCA",

    # Connective Tissue & Skeletal
    "marfan syndrome": "FBN1",
    "marfan": "FBN1",
    "ehlers-danlos syndrome": "COL5A1",
    "ehlers danlos": "COL5A1",
    "eds": "COL5A1",
    "osteogenesis imperfecta": "COL1A1",
    "brittle bone disease": "COL1A1",
    "oi": "COL1A1",
    "stickler syndrome": "COL2A1",
    "stickler": "COL2A1",
    "achondroplasia": "FGFR3",

    # Immunodeficiencies
    "severe combined immunodeficiency": "IL2RG",
    "scid": "IL2RG",
    "x-linked agammaglobulinemia": "BTK",
    "xla": "BTK",
    "bruton agammaglobulinemia": "BTK",
    "wiskott-aldrich syndrome": "WAS",
    "wiskott aldrich": "WAS",
    "was": "WAS",
    "digeorge syndrome": "TBX1",
    "digeorge": "TBX1",

    # Inborn Errors of Metabolism
    "phenylketonuria": "PAH",
    "pku": "PAH",
    "wilson disease": "ATP7B",
    "wilson's disease": "ATP7B",
    "wilson": "ATP7B",
    "maple syrup urine disease": "BCKDHA",
    "msud": "BCKDHA",
    "galactosemia": "GALT",
    "homocystinuria": "CBS",
    "medium-chain acyl-coa dehydrogenase deficiency": "ACADM",
    "mcad deficiency": "ACADM",
    "mcadd": "ACADM",
    "glycogen storage disease type i": "G6PC1",
    "von gierke disease": "G6PC1",
    "gsd1": "G6PC1",
    "biotinidase deficiency": "BTD",
    "propionic acidemia": "PCCA",

    # Cardiac Channelopathies & Cardiomyopathies
    "long qt syndrome": "KCNQ1",
    "lqts": "KCNQ1",
    "hypertrophic cardiomyopathy": "MYH7",
    "hcm": "MYH7",
    "dilated cardiomyopathy": "LMNA",
    "dcm": "LMNA",
    "brugada syndrome": "SCN5A",
    "brugada": "SCN5A",
    "arrhythmogenic right ventricular cardiomyopathy": "PKP2",
    "arvc": "PKP2",
    "catecholaminergic polymorphic ventricular tachycardia": "RYR2",
    "cpvt": "RYR2",

    # Pulmonary
    "cystic fibrosis": "CFTR",
    "cf": "CFTR",
    "alpha-1 antitrypsin deficiency": "SERPINA1",
    "alpha 1 antitrypsin deficiency": "SERPINA1",
    "aatd": "SERPINA1",
    "a1at": "SERPINA1",
    "primary ciliary dyskinesia": "DNAI1",
    "pcd": "DNAI1",

    # Renal
    "polycystic kidney disease": "PKD1",
    "autosomal dominant polycystic kidney disease": "PKD1",
    "adpkd": "PKD1",
    "pkd": "PKD1",
    "alport syndrome": "COL4A5",
    "alport": "COL4A5",

    # Ophthalmic
    "retinitis pigmentosa": "RHO",
    "rp": "RHO",
    "leber congenital amaurosis": "RPE65",
    "lca": "RPE65",
    "stargardt disease": "ABCA4",
    "stargardt": "ABCA4",

    # Cancer Predisposition & Tumor Syndromes
    "neurofibromatosis type 1": "NF1",
    "neurofibromatosis": "NF1",
    "nf1": "NF1",
    "neurofibromatosis type 2": "NF2",
    "nf2": "NF2",
    "li-fraumeni syndrome": "TP53",
    "li fraumeni": "TP53",
    "familial adenomatous polyposis": "APC",
    "fap": "APC",
    "von hippel-lindau disease": "VHL",
    "von hippel-lindau": "VHL",
    "vhl": "VHL",
    "tuberous sclerosis": "TSC1",
    "tsc": "TSC1",
    "retinoblastoma": "RB1",

    # Syndromic & Other Rare Conditions
    "williams syndrome": "ELN",
    "williams": "ELN",
    "noonan syndrome": "PTPN11",
    "noonan": "PTPN11",
    "alagille syndrome": "JAG1",
    "alagille": "JAG1",
    "kabuki syndrome": "KMT2D",
    "kabuki": "KMT2D",
    "cornelia de lange syndrome": "NIPBL",
    "cdls": "NIPBL",
    "hutchinson-gilford progeria": "LMNA",
    "progeria": "LMNA",
}


class DiseaseResolverEngine:

    def __init__(self):
        self.cache = DiseaseCache()
        self.ncbi = NCBIGeneClient()

    @staticmethod
    def _gene_symbol(disease: Any) -> Optional[str]:
        """Extract explicit gene_symbol if set on Disease model or dict."""
        if isinstance(disease, dict):
            sym = disease.get("gene_symbol")
        else:
            sym = getattr(disease, "gene_symbol", None)
        return str(sym).strip().upper() if sym else None

    @staticmethod
    def _name(disease: Any) -> str:
        if isinstance(disease, str):
            return disease.strip()
        name = getattr(disease, "name", None)
        if not name and isinstance(disease, dict):
            name = disease.get("name")
        if not name:
            raise ValueError(f"Cannot resolve disease from {disease!r}")
        return str(name).strip()

    def resolve(self, disease: Any) -> str:
        # 1. Option A: Bypass Resolver if explicit gene symbol provided
        explicit_gene = self._gene_symbol(disease)
        if explicit_gene:
            print(f"✓ Using explicit target gene symbol: {explicit_gene}")
            return explicit_gene

        name = self._name(disease)
        norm_key = name.lower().strip()

        # 2. Option B: Check curated disease/acronym -> HGNC symbol mapping
        if norm_key in KNOWN_DISEASE_MAP:
            gene = KNOWN_DISEASE_MAP[norm_key]
            self.cache.save(norm_key, gene)
            print(f"✓ Mapped '{name}' -> {gene} (via curated disease map / HGNC)")
            return gene

        # 3. Check cache
        cached = self.cache.get(name)
        if cached:
            # Defensive check: ensure DMD is never mapped to ERBB2 from stale cache
            if norm_key in ("dmd", "duchenne", "duchenne muscular dystrophy") and cached.upper() != "DMD":
                print(f"⚠ Stale cache mapping '{name}' -> {cached} detected. Purging...")
                cached = None
            else:
                print(f"✓ '{name}' loaded from cache -> {cached}")
                return cached

        # 4. Fallback to NCBI Gene resolution
        try:
            gene = self.ncbi.disease_to_gene(name)
        except (HTTPError, ValueError) as exc:
            raise RuntimeError(
                f"Disease resolution failed for '{name}': {exc}"
            ) from exc

        self.cache.save(name, gene)
        print(f"✓ Resolved '{name}' -> {gene}")
        return gene
