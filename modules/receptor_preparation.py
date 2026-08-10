import os
import subprocess


class ReceptorPreparation:

    def prepare(self, pdb_file):

        output = (
            pdb_file
            .replace(".pdb", ".pdbqt")
        )

        if os.path.exists(output):
            return output

        print("Preparing receptor...")

        command = [
            "obabel",
            pdb_file,
            "-O",
            output
        ]

        subprocess.run(
            command,
            check=True
        )

        return output
