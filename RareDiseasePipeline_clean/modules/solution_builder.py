import shutil
from pathlib import Path

from clients.gromacs import GromacsClient
from clients.ambertools import AmberToolsClient



class SolutionBuilder:


    def __init__(self):

        self.gmx = GromacsClient()

        self.amber = AmberToolsClient()



    def build(self, context):


        print("\nPreparing simulation system...")


        simulation_dir = Path(
            "simulations"
        )


        if simulation_dir.exists():

            shutil.rmtree(
                simulation_dir
            )


        simulation_dir.mkdir(
            parents=True
        )



        candidates = context.get("ranked_candidates", [])
	
        
        if not candidates:
            print("No drug candidates available. Skipping MD system generation.")
            return {
                "status": "skipped",
                "reason": "No drug candidates"
            }
	
        candidate = candidates[0]
        affinity = candidate.get("affinity")

        if affinity is None or affinity >= 0:
            print(f"\n⚠️ Top candidate docking score ({affinity}) is non-binding (>= 0 kcal/mol).")
            print("Skipping MD system generation.")
            return {
                "status": "skipped",
                "reason": f"Docking score ({affinity}) is non-binding"
            }

        if affinity <= -7.0:
            print(f"\n✅ Top candidate docking score ({affinity:.2f} kcal/mol) meets <= -7.0 kcal/mol threshold. Building MD simulation system...")
        else:
            print(f"\n📌 Fallback: No candidate reached <= -7.0 kcal/mol. Selecting candidate with highest negative docking score ({affinity:.2f} kcal/mol) for MD simulation system building...")
            # Sanity gate: ensure QED is sufficient for fallback candidate
            qed = candidate.get('evaluation', {}).get('qed')
            if qed is None or qed < 0.35:
                print(f"⚠️ Fallback candidate QED ({qed}) below 0.35 threshold. Skipping MD system generation.")
                return {"status": "skipped", "reason": "Low QED in fallback candidate"}


        protein = context[
            "protein"
        ]



        pdb_file = context[
            "pdb_file"
        ]


        ligand = candidate[
            "ligand"
        ]



        protein_name = getattr(

            protein,

            "name",

            protein.protein_id

        )


        print(
            f"Protein : {protein_name}"
        )


        print(
            f"Ligand  : {ligand.name}"
        )



        try:
            # -----------------------------
            # Step 1 : Export ligand
            # -----------------------------
            self.export_ligand(ligand, simulation_dir)

            # -----------------------------
            # Step 2 : Prepare protein
            # -----------------------------
            self.prepare_protein(pdb_file, simulation_dir)

            # -----------------------------
            # Step 3 : Ligand parameters
            # -----------------------------
            self.parameterize_ligand(simulation_dir)

            # -----------------------------
            # Step 4 : Complex
            # -----------------------------
            self.build_complex(simulation_dir)

            # -----------------------------
            # Step 5 : Box
            # -----------------------------
            self.create_box(simulation_dir)

            # -----------------------------
            # Step 6 : Solvation
            # -----------------------------
            self.solvate(simulation_dir)

            # -----------------------------
            # Step 7 : Ions
            # -----------------------------
            self.add_ions(simulation_dir)

            # -----------------------------
            # Step 8 : Topology
            # -----------------------------
            self.generate_topology(simulation_dir)

            # -----------------------------
            # Step 9 : MDP
            # -----------------------------
            self.generate_mdp_files(simulation_dir)

            # -----------------------------
            # Step 10 : Run script
            # -----------------------------
            self.generate_run_script(simulation_dir)

        except Exception as e:
            print("\n❌ Biological problem: The available files are not completed or fragmented.")
            print(f"Unable to process this structure for simulation. Skipping MD system generation.")
            print(f"Error Details: {e}")
            return {
                "status": "skipped",
                "reason": "Biological structural error (fragmented files)"
            }

        print(
            "\nSimulation prepared successfully."
        )


        return {

            "simulation_directory":
                str(simulation_dir),


            "protein":
                protein_name,


            "ligand":
                ligand.name

        }





    def export_ligand(self, ligand, outdir):

        self.amber.export_ligand(
            ligand,
            outdir
        )



    def prepare_protein(self, pdb_file, outdir):

        self.gmx.prepare_protein(
            pdb_file,
            outdir
        )



    def parameterize_ligand(self, outdir):

        self.amber.parameterize(
            outdir
        )



    def build_complex(self, outdir):

        self.gmx.build_complex(
            outdir
        )



    def create_box(self, outdir):

        self.gmx.create_box(
            outdir
        )



    def solvate(self, outdir):

        self.gmx.solvate(
            outdir
        )



    def add_ions(self, outdir):

        self.gmx.add_ions(
            outdir
        )



    def generate_topology(self, outdir):

        self.gmx.generate_topology(
            outdir
        )



    def generate_mdp_files(self, outdir):

        self.gmx.generate_mdp_files(
            outdir
        )



    def generate_run_script(self, outdir):

        self.gmx.generate_run_script(
            outdir
        )
