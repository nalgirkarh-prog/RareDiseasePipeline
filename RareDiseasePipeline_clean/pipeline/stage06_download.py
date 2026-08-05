import subprocess
from clients.downloader import StructureDownloader
from models.structure import Structure


class DownloadStage:

    def __init__(self):
        self.client = StructureDownloader()

    def _fix_pdb(self, filepath):
        print(f"  Running PDBFixer on {filepath}...")
        outfile = filepath.replace(".pdb", "_fixed.pdb")
        try:
            subprocess.run([
                "pdbfixer", filepath,
                f"--output={outfile}",
                "--add-atoms=all",
                "--add-residues",
                "--replace-nonstandard"
            ], check=True, capture_output=True)
            return outfile
        except Exception as e:
            print(f"  ⚠ PDBFixer failed, using original file. Error: {e}")
            return filepath

    def run(self, protein, structure):

        # Experimental structure available
        if structure is not None and structure.pdb_id is not None:

            print(f"\nDownloading PDB {structure.pdb_id}...")

            file = self.client.download_pdb(
                structure.pdb_id
            )
            
            if file:
                file = self._fix_pdb(file)

            structure.file_path = file

            return structure

        # AlphaFold fallback
        if protein.uniprot:

            print("\nDownloading AlphaFold model...")

            file = self.client.download_alphafold(
                protein.uniprot
            )

            if file:
                file = self._fix_pdb(file)
                
                if structure is None:
                    structure = Structure()

                structure.file_path = file
                structure.pdb_id = f"AF_{protein.uniprot}"

        return structure
