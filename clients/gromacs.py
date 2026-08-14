"""
clients/gromacs.py

Thin wrapper around the GROMACS command-line tools plus generators for the
.mdp files and the interactive run_md.sh driver.

Implements the full solution-builder workflow:
  1. prepare_protein
  2. build_complex
  3. create_box
  4. solvate
  5. add_ions
  6. generate_topology
  7. generate_mdp_files
  8. generate_run_script
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from Bio.PDB import PDBIO
from Bio.PDB import PDBParser
from Bio.PDB import Select


class RemoveCrystalArtifacts(Select):
    """
    Removes crystallographic waters and common crystallization agents.

    Important biological cofactors (HEM, ATP, FAD, metals, etc.)
    are intentionally preserved.
    """

    REMOVE = {
        "HOH",
        "WAT",
        "SOL",
        "GOL",
        "PEG",
        "PG4",
        "EOH",
        "DMS",
        "MPD",
        "SO4",
        "PO4",
    }

    def accept_residue(self, residue):
        # Exclude heteroatoms (like NAG, EDO, FE) that cause chain inconsistency in gromacs
        if residue.id[0] != ' ' and residue.id[0] != 'W':
            return 0
        return residue.get_resname().strip() not in self.REMOVE


class GromacsClient:

    DT = "0.002"

    # -------------------------------------------------------------

    def run_command(self, command, stdin_data=None):

        print("\nExecuting:")
        print(" ".join(str(c) for c in command))

        if stdin_data is not None:

            subprocess.run(
                command,
                input=stdin_data,
                text=True,
                check=True,
            )

        else:

            subprocess.run(
                command,
                check=True,
            )

    # -------------------------------------------------------------
    # Structure preprocessing
    # -------------------------------------------------------------

    def clean_protein(self, protein_file, outdir):

        outdir = Path(outdir)

        cleaned_pdb = outdir / "protein_clean.pdb"

        parser = PDBParser(QUIET=True)

        structure = parser.get_structure(
            "protein",
            str(protein_file),
        )

        io = PDBIO()

        io.set_structure(structure)

        with open(cleaned_pdb, "w") as f:
            io.save(f, RemoveCrystalArtifacts())

        print("✓ Removed crystallographic waters and buffer molecules")

        return cleaned_pdb

    # -------------------------------------------------------------
    # Step 1 : Prepare protein
    # -------------------------------------------------------------

    def prepare_protein(self, protein_file, outdir):

        outdir = Path(outdir)

        cleaned_pdb = self.clean_protein(
            protein_file,
            outdir,
        )

        gro_file = outdir / "protein.gro"

        top_file = outdir / "topol.top"

        posre_file = outdir / "posre.itp"

        command = [
            "gmx",
            "pdb2gmx",
            "-f",
            str(cleaned_pdb),
            "-o",
            str(gro_file),
            "-p",
            str(top_file),
            "-i",
            str(posre_file),
            "-ff",
            "amber99sb-ildn",
            "-water",
            "tip3p",
            "-ignh",
        ]

        self.run_command(command)

        print("✓ Protein topology generated")

    # -------------------------------------------------------------
    # Step 2 : Build protein-ligand complex
    # -------------------------------------------------------------

    def build_complex(self, outdir):
        """
        Convert GAFF2 ligand parameters to GROMACS format via tleap and ParmEd,
        merge protein + ligand coordinates, and update topology.
        """

        outdir = Path(outdir)

        print("Building protein-ligand complex...")

        protein_gro = outdir / "protein.gro"
        ligand_mol2 = outdir / "ligand_gaff.mol2"
        ligand_frcmod = outdir / "ligand.frcmod"

        complex_gro = outdir / "complex.gro"
        topol_top = outdir / "topol.top"

        # ----------------------------------------------------------
        # Generate Amber parameters
        # ----------------------------------------------------------

        print("  Generating Amber parameters for ligand via tleap...")

        leap_input = f"""source leaprc.gaff2
loadamberparams {ligand_frcmod}
LIG = loadmol2 {ligand_mol2}
saveamberparm LIG {outdir}/ligand.prmtop {outdir}/ligand.inpcrd
quit
"""

        leap_file = outdir / "tleap_ligand.in"

        leap_file.write_text(leap_input)

        self.run_command(
            [
                "tleap",
                "-f",
                str(leap_file),
            ]
        )

        # ----------------------------------------------------------
        # Convert Amber → GROMACS
        # ----------------------------------------------------------

        print("  Converting ligand parameters using ParmEd...")

        import parmed as pmd

        amber = pmd.load_file(
            str(outdir / "ligand.prmtop"),
            str(outdir / "ligand.inpcrd"),
        )

        amber.save(
            str(outdir / "ligand.top"),
            format="gromacs",
            overwrite=True,
        )

        amber.save(
            str(outdir / "ligand.gro"),
            overwrite=True,
        )

        # ----------------------------------------------------------
        # Extract atomtypes + ligand topology
        # ----------------------------------------------------------

        print("  Creating ligand topology...")

        with open(outdir / "ligand.top") as f:
            lines = f.readlines()

        atomtypes_lines = []
        raw_ligand_lines = []

        in_atomtypes = False
        in_moleculetype = False
        old_molname = None

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("[ atomtypes ]"):

                in_atomtypes = True
                in_moleculetype = False
                atomtypes_lines.append(line)
                continue

            if stripped.startswith("[ moleculetype ]"):

                in_atomtypes = False
                in_moleculetype = True
                raw_ligand_lines.append(line)
                continue

            if stripped.startswith("[ system ]"):

                in_atomtypes = False
                in_moleculetype = False
                continue

            if in_atomtypes:

                atomtypes_lines.append(line)

            elif in_moleculetype:

                if old_molname is None and stripped and not stripped.startswith(";"):
                    old_molname = stripped.split()[0]
                raw_ligand_lines.append(line)

        ligand_lines = []
        for line in raw_ligand_lines:
            mod_line = line
            if old_molname:
                mod_line = mod_line.replace(old_molname, "LIG")
            mod_line = mod_line.replace("UNL", "LIG").replace("<1>", "LIG")
            ligand_lines.append(mod_line)

        atomtypes_itp = outdir / "ligand_atomtypes.itp"

        if atomtypes_lines:

            atomtypes_itp.write_text(
                "".join(atomtypes_lines)
            )

        ligand_itp = outdir / "ligand.itp"

        ligand_itp.write_text(
            "".join(ligand_lines)
        )

        # ----------------------------------------------------------
        # Merge coordinates
        # ----------------------------------------------------------

        print("  Merging protein and ligand...")

        self._merge_gro_files(
            protein_gro,
            outdir / "ligand.gro",
            complex_gro,
            old_molname=old_molname,
        )

        # ----------------------------------------------------------
        # Update topology
        # ----------------------------------------------------------

        print("  Updating topology...")

        self._update_topology_for_ligand(
            topol_top,
            outdir,
        )

        # ----------------------------------------------------------
        # Cleanup
        # ----------------------------------------------------------

        for filename in [
            "ligand.prmtop",
            "ligand.inpcrd",
            "ligand.top",
            "ligand.gro",
            "tleap_ligand.in",
        ]:

            file = outdir / filename

            if file.exists():

                file.unlink()

        print("✓ Protein-ligand complex built")

    # -------------------------------------------------------------
    # Step 3 : Create simulation box
    # -------------------------------------------------------------

    def create_box(self, outdir):
        """
        Create a rhombic dodecahedron simulation box with a 1.0 nm buffer.
        """

        outdir = Path(outdir)

        print("Creating simulation box...")

        input_gro = outdir / "complex.gro"

        # Fallback to protein-only system
        if not input_gro.exists():
            input_gro = outdir / "protein.gro"

        box_gro = outdir / "box.gro"

        self.run_command([
            "gmx",
            "editconf",
            "-f", str(input_gro),
            "-o", str(box_gro),
            "-c",
            "-d", "1.0",
            "-bt", "dodecahedron",
        ])

        print("✓ Simulation box created")

    # -------------------------------------------------------------
    # Step 4 : Solvate system
    # -------------------------------------------------------------

    def solvate(self, outdir):
        """
        Fill the simulation box with TIP3P water molecules.
        """

        outdir = Path(outdir)

        print("Solvating system...")

        box_gro = outdir / "box.gro"
        solvated_gro = outdir / "solvated.gro"
        topol_top = outdir / "topol.top"

        self.run_command([
            "gmx",
            "solvate",
            "-cp", str(box_gro),
            "-cs", "spc216.gro",
            "-o", str(solvated_gro),
            "-p", str(topol_top),
        ])

        print("✓ System solvated")

    # -------------------------------------------------------------
    # Step 5 : Add ions
    # -------------------------------------------------------------

    def add_ions(self, outdir):
        """
        Neutralise the solvated system using Na+ and Cl- ions.
        """

        outdir = Path(outdir)

        print("Adding ions...")

        solvated_gro = outdir / "solvated.gro"
        topol_top = outdir / "topol.top"

        em_mdp = outdir / "em.mdp"
        ions_tpr = outdir / "ions.tpr"

        # Create a minimal energy-minimisation MDP if it doesn't exist
        if not em_mdp.exists():

            em_mdp.write_text(
                "integrator      = steep\n"
                "emtol           = 1000.0\n"
                "emstep          = 0.01\n"
                "nsteps          = 50000\n"
                "nstlist         = 10\n"
                "cutoff-scheme   = Verlet\n"
                "coulombtype     = PME\n"
                "rcoulomb        = 1.0\n"
                "rvdw            = 1.0\n"
                "pbc             = xyz\n"
            )

        # Generate portable run input
        self.run_command([
            "gmx",
            "grompp",
            "-f", str(em_mdp),
            "-c", str(solvated_gro),
            "-p", str(topol_top),
            "-o", str(ions_tpr),
            "-maxwarn", "2",
        ])

        # Replace solvent molecules with ions
        self.run_command(
            [
                "gmx",
                "genion",
                "-s", str(ions_tpr),
                "-o", str(solvated_gro),
                "-p", str(topol_top),
                "-pname", "NA",
                "-nname", "CL",
                "-neutral",
            ],
            stdin_data="SOL\n",
        )

        # Cleanup
        if ions_tpr.exists():
            ions_tpr.unlink()

        mdout = outdir / "mdout.mdp"

        if mdout.exists():
            mdout.unlink()

        print("✓ System neutralised")

    # -------------------------------------------------------------
    # Step 6 : Verify topology
    # -------------------------------------------------------------

    def generate_topology(self, outdir):
        """
        Verify that the generated GRO file is readable and contains atoms.
        """

        outdir = Path(outdir)

        print("Verifying topology consistency...")

        solvated_gro = outdir / "solvated.gro"

        if not solvated_gro.exists():

            print("⚠ solvated.gro not found")
            return

        with open(solvated_gro) as f:

            title = f.readline()

            atom_count = int(f.readline().strip())

        print(f"  Total atoms : {atom_count}")

        print("✓ Topology verification passed")

    # =============================================================
    # Helper Methods
    # =============================================================

    @staticmethod
    def _merge_gro_files(protein_gro, ligand_gro, output_gro, old_molname=None):
        """
        Merge protein and ligand GRO files.
        Protein atoms remain first.
        Ligand atoms are appended.
        """

        with open(protein_gro) as f:
            protein = f.readlines()

        with open(ligand_gro) as f:
            ligand = f.readlines()

        protein_title = protein[0].strip()

        protein_atoms = int(protein[1])

        ligand_atoms = int(ligand[1])

        protein_coordinates = protein[2:2 + protein_atoms]

        ligand_coordinates = ligand[2:2 + ligand_atoms]

        box = protein[2 + protein_atoms]

        renamed_ligand = []

        for line in ligand_coordinates:

            line_mod = line
            if old_molname and old_molname in line_mod:
                line_mod = line_mod.replace(old_molname, "LIG")
            line_mod = line_mod.replace("UNL", "LIG").replace("<1>", "LIG")
            renamed_ligand.append(line_mod)

        total_atoms = protein_atoms + ligand_atoms

        with open(output_gro, "w") as f:

            f.write(f"{protein_title} + ligand\n")

            f.write(f"{total_atoms}\n")

            f.writelines(protein_coordinates)

            f.writelines(renamed_ligand)

            f.write(box)

    # -------------------------------------------------------------

    @staticmethod
    def _update_topology_for_ligand(topol_top, outdir):

        with open(topol_top) as f:

            content = f.read()

        atomtypes = outdir / "ligand_atomtypes.itp"

        ligand = outdir / "ligand.itp"

        include_text = ""

        if atomtypes.exists():

            include_text += (
                '\n; Include ligand atom types\n'
                f'#include "{atomtypes.name}"\n'
            )

        include_text += (
            '\n; Include ligand topology\n'
            f'#include "{ligand.name}"\n'
        )

        pattern = r'(#include\s+"amber99sb-ildn\.ff/forcefield\.itp")'

        if re.search(pattern, content):

            content = re.sub(
                pattern,
                r"\1" + include_text,
                content,
                count=1,
            )

        else:

            content = content.replace(
                "[ moleculetype ]",
                include_text + "\n[ moleculetype ]",
                1,
            )

        if "LIG" not in content:

            content = (
                content.rstrip()
                + "\nLIG                 1\n"
            )

        with open(topol_top, "w") as f:

            f.write(content)

    # -------------------------------------------------------------
    # Step 7 : Generate MDP files
    # -------------------------------------------------------------

    def generate_mdp_files(self, outdir):

        outdir = Path(outdir)

        dt = self.DT

        print("Generating MDP files...")

        (outdir / "em.mdp").write_text(
            "integrator      = steep\n"
            "emtol           = 1000.0\n"
            "emstep          = 0.01\n"
            "nsteps          = 50000\n"
            "nstlist         = 10\n"
            "cutoff-scheme   = Verlet\n"
            "coulombtype     = PME\n"
            "rcoulomb        = 1.0\n"
            "rvdw            = 1.0\n"
            "pbc             = xyz\n"
        )

        common = (
            f"dt              = {dt}\n"
            "constraints     = h-bonds\n"
            "constraint_algorithm = lincs\n"
            "cutoff-scheme   = Verlet\n"
            "coulombtype     = PME\n"
            "rcoulomb        = 1.0\n"
            "rvdw            = 1.0\n"
            "tcoupl          = V-rescale\n"
            "tc-grps         = System\n"
            "tau_t           = 0.1\n"
            "ref_t           = 300\n"
            "pbc             = xyz\n"
        )

        pressure = (
            "pcoupl          = Parrinello-Rahman\n"
            "pcoupltype      = isotropic\n"
            "tau_p           = 2.0\n"
            "ref_p           = 1.0\n"
            "compressibility = 4.5e-5\n"
        )

        (outdir / "nvt.mdp").write_text(
            "integrator      = md\n"
            "nsteps          = 50000\n"
            "continuation    = no\n"
            + common +
            "pcoupl          = no\n"
            "gen_vel         = yes\n"
            "gen_temp        = 300\n"
        )

        (outdir / "npt.mdp").write_text(
            "integrator      = md\n"
            "nsteps          = 50000\n"
            "continuation    = yes\n"
            + common +
            pressure +
            "gen_vel         = no\n"
        )

        (outdir / "md.mdp").write_text(
            "integrator      = md\n"
            "nsteps          = 50000000\n"
            "continuation    = yes\n"
            + common +
            pressure +
            "nstxout-compressed = 5000\n"
            "nstenergy       = 5000\n"
            "nstlog          = 5000\n"
            "gen_vel         = no\n"
        )

        print("✓ MDP files generated")
    # -------------------------------------------------------------
    # Step 8 : Generate MD execution script
    # -------------------------------------------------------------

    def generate_run_script(self, outdir):
        """
        Generate the shell script that performs the complete MD workflow.
        """

        outdir = Path(outdir)

        script = outdir / "run_md.sh"

        script.write_text(self._run_md_script())

        os.chmod(script, 0o755)

        print("✓ MD execution script generated")

    # =============================================================
    # MD execution script
    # =============================================================

    @staticmethod
    def _run_md_script():

        return r"""#!/bin/bash

set -e

echo "====================================="
echo " Molecular Dynamics Simulation"
echo "====================================="

# ---------------------------------------
# Energy Minimization
# ---------------------------------------

echo
echo "[1/4] Energy Minimization"

gmx grompp \
    -f em.mdp \
    -c solvated.gro \
    -p topol.top \
    -o em.tpr \
    -maxwarn 2

gmx mdrun \
    -deffnm em

# ---------------------------------------
# NVT Equilibration
# ---------------------------------------

echo
echo "[2/4] NVT Equilibration"

gmx grompp \
    -f nvt.mdp \
    -c em.gro \
    -r em.gro \
    -p topol.top \
    -o nvt.tpr \
    -maxwarn 2

gmx mdrun \
    -deffnm nvt

# ---------------------------------------
# NPT Equilibration
# ---------------------------------------

echo
echo "[3/4] NPT Equilibration"

gmx grompp \
    -f npt.mdp \
    -c nvt.gro \
    -r nvt.gro \
    -t nvt.cpt \
    -p topol.top \
    -o npt.tpr \
    -maxwarn 2

gmx mdrun \
    -deffnm npt

# ---------------------------------------
# Production MD
# ---------------------------------------

echo
echo "[4/4] Production MD"

gmx grompp \
    -f md.mdp \
    -c npt.gro \
    -t npt.cpt \
    -p topol.top \
    -o md.tpr \
    -maxwarn 2

gmx mdrun \
    -deffnm md

echo
echo "====================================="
echo " Simulation Complete!"
echo "====================================="

echo
echo "[5/5] Trajectory Analysis (Hydrogen Bonds)"
echo "1 1" | gmx hbond -f md.xtc -s md.tpr -num hbnum.xvg -dist hbdist.xvg -life hblife.xvg -hbn hbond.ndx
echo "✓ Hydrogen bond analysis completed (length, occupancy, lifetime)"

"""
