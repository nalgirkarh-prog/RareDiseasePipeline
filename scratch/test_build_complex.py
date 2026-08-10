import re
import shutil
import subprocess
from pathlib import Path
import parmed as pmd

sim_dir = Path("/home/harsh/Downloads/RareDiseasePipeline_clean/output/simulation")

# Backup topol.top and protein.gro before test
shutil.copy2(sim_dir / "topol.top", sim_dir / "topol.top.bak")

def build_complex():
    protein_gro = sim_dir / "protein.gro"
    ligand_mol2 = sim_dir / "ligand_gaff.mol2"
    ligand_frcmod = sim_dir / "ligand.frcmod"
    complex_gro = sim_dir / "complex.gro"
    topol_top = sim_dir / "topol.top"

    # --- 1. Run tleap to generate Amber parameters for ligand -----------
    print("Running tleap...")
    leap_input = f"""source leaprc.gaff2
loadamberparams {ligand_frcmod}
LIG = loadmol2 {ligand_mol2}
saveamberparm LIG {sim_dir}/ligand.prmtop {sim_dir}/ligand.inpcrd
quit
"""
    leap_in_file = sim_dir / "tleap_ligand.in"
    leap_in_file.write_text(leap_input)
    subprocess.run(["tleap", "-f", str(leap_in_file)], check=True)

    # --- 2. Run parmed to convert to GROMACS topology/coordinates ------
    print("Running parmed...")
    amber = pmd.load_file(str(sim_dir / "ligand.prmtop"), str(sim_dir / "ligand.inpcrd"))
    amber.save(str(sim_dir / "ligand.top"), format="gromacs", overwrite=True)
    amber.save(str(sim_dir / "ligand.gro"), overwrite=True)

    # --- 3. Parse ligand.top to extract atomtypes and moleculetype ----
    print("Parsing ligand.top...")
    with open(sim_dir / "ligand.top") as f:
        lines = f.readlines()

    atomtypes_lines = []
    moleculetype_lines = []

    in_atomtypes = False
    in_moleculetype = False

    for line in lines:
        if line.strip().startswith("[ atomtypes ]"):
            in_atomtypes = True
            in_moleculetype = False
            atomtypes_lines.append(line)
            continue
        elif line.strip().startswith("[ moleculetype ]"):
            in_atomtypes = False
            in_moleculetype = True
            moleculetype_lines.append(line)
            continue
        elif line.strip().startswith("[ system ]"):
            in_atomtypes = False
            in_moleculetype = False
            continue

        if in_atomtypes:
            atomtypes_lines.append(line)
        elif in_moleculetype:
            renamed_line = line.replace("UNL", "LIG")
            moleculetype_lines.append(renamed_line)

    # Write itp files
    atomtypes_itp = sim_dir / "ligand_atomtypes.itp"
    if atomtypes_lines:
        atomtypes_itp.write_text("".join(atomtypes_lines))
        print("  Wrote ligand_atomtypes.itp")
    else:
        print("  No custom atomtypes found")

    ligand_itp = sim_dir / "ligand.itp"
    ligand_itp.write_text("".join(moleculetype_lines))
    print("  Wrote ligand.itp")

    # --- 4. Merge coordinates (renaming UNL to LIG in ligand.gro) -----
    print("Merging gro files...")
    with open(protein_gro) as f:
        prot_lines = f.readlines()

    with open(sim_dir / "ligand.gro") as f:
        lig_lines = f.readlines()

    prot_title = prot_lines[0].strip()
    prot_natoms = int(prot_lines[1].strip())
    prot_atoms = prot_lines[2:2 + prot_natoms]
    prot_box = prot_lines[2 + prot_natoms]

    lig_natoms = int(lig_lines[1].strip())
    lig_atoms = lig_lines[2:2 + lig_natoms]

    renamed_lig_atoms = []
    for line in lig_atoms:
        renamed_line = line.replace("UNL", "LIG")
        renamed_lig_atoms.append(renamed_line)

    total_atoms = prot_natoms + lig_natoms

    with open(complex_gro, "w") as f:
        f.write(f"{prot_title} + ligand\n")
        f.write(f"{total_atoms}\n")
        for line in prot_atoms:
            f.write(line)
        for line in renamed_lig_atoms:
            f.write(line)
        f.write(prot_box)
    print("  Wrote complex.gro")

    # --- 5. Update topol.top ----------------------------------------
    print("Updating topol.top...")
    with open(topol_top) as f:
        content = f.read()

    # Insert includes
    includes = ""
    if atomtypes_itp.exists():
        includes += f'\n; Include ligand atom types\n#include "ligand_atomtypes.itp"\n'
    includes += f'\n; Include ligand topology\n#include "ligand.itp"\n'

    # Insert after forcefield.itp include
    ff_pattern = r'(#include\s+"amber99sb-ildn\.ff/forcefield\.itp")'
    if re.search(ff_pattern, content):
        content = re.sub(ff_pattern, r'\1' + includes, content, count=1)
    else:
        content = content.replace("[ moleculetype ]", includes + "\n[ moleculetype ]", 1)

    # Append LIG to molecules section
    if "LIG" not in content:
        content = content.rstrip("\n") + "\nLIG                 1\n"

    with open(topol_top, "w") as f:
        f.write(content)
    print("  Updated topol.top")

build_complex()
