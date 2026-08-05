from clients.fpocket import FPocketClient
from modules.pocket_analysis import PocketAnalyzer
import os


class PocketDetector:

    def __init__(self):

        self.client = FPocketClient()

        self.analyzer = PocketAnalyzer()



    def run(self, pdb_file):

        print("▶ Detecting binding pockets")


        pockets = self.detect(
            pdb_file
        )


        print(
            f"✓ Detected {len(pockets)} pockets"
        )


        return pockets




    def detect(self, pdb_file):

        output_folder = self.client.run(
            pdb_file
        )


        info_file = os.path.join(
            output_folder,
            os.path.basename(
                pdb_file
            ).replace(
                ".pdb",
                "_info.txt"
            )
        )


        pocket_folder = os.path.join(
            output_folder,
            "pockets"
        )


        pockets = self.analyzer.parse_info(
            info_file,
            pocket_folder
        )


        return pockets
