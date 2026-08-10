import subprocess
from pathlib import Path

sim_dir = Path("/home/harsh/Downloads/RareDiseasePipeline_clean/output/simulation")

def run_cmd(args, stdin_data=None):
    print("Running:", " ".join(args))
    if stdin_data:
        res = subprocess.run(args, input=stdin_data, text=True, capture_output=True)
    else:
        res = subprocess.run(args, capture_output=True, text=True)
    print("STDOUT:", res.stdout[-300:] if res.stdout else "")
    print("STDERR:", res.stderr[-500:] if res.stderr else "")
    res.check_returncode()

# Step 5: Editconf
run_cmd([
    "gmx", "editconf",
    "-f", str(sim_dir / "complex.gro"),
    "-o", str(sim_dir / "box.gro"),
    "-c",
    "-d", "1.0",
    "-bt", "dodecahedron"
])

# Step 6: Solvate
run_cmd([
    "gmx", "solvate",
    "-cp", str(sim_dir / "box.gro"),
    "-cs", "spc216.gro",
    "-o", str(sim_dir / "solvated.gro"),
    "-p", str(sim_dir / "topol.top")
])

# Step 7: Grompp & Genion
# Write a temporary em.mdp for grompp
em_mdp = sim_dir / "em.mdp"
if not em_mdp.exists():
    em_mdp.write_text(
        "integrator  = steep\n"
        "emtol       = 1000.0\n"
        "emstep      = 0.01\n"
        "nsteps      = 50000\n"
        "nstlist     = 10\n"
        "cutoff-scheme = Verlet\n"
        "coulombtype = PME\n"
        "rcoulomb    = 1.0\n"
        "rvdw        = 1.0\n"
        "pbc         = xyz\n"
    )

run_cmd([
    "gmx", "grompp",
    "-f", str(em_mdp),
    "-c", str(sim_dir / "solvated.gro"),
    "-p", str(sim_dir / "topol.top"),
    "-o", str(sim_dir / "ions.tpr"),
    "-maxwarn", "2"
])

run_cmd([
    "gmx", "genion",
    "-s", str(sim_dir / "ions.tpr"),
    "-o", str(sim_dir / "solvated.gro"),
    "-p", str(sim_dir / "topol.top"),
    "-pname", "NA",
    "-nname", "CL",
    "-neutral"
], stdin_data="SOL\n")

print("All GROMACS steps tested successfully!")
