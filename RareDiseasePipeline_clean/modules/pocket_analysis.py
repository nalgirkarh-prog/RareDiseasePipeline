import re
from models.pocket import Pocket


class PocketAnalyzer:


    def parse_info(self, info_file, pocket_folder):

        pockets = []


        with open(info_file) as f:

            content = f.read()


        blocks = content.split("Pocket ")[1:]


        for i, block in enumerate(blocks, start=1):

            def extract(pattern):

                match = re.search(
                    pattern,
                    block
                )

                if match:
                    return float(match.group(1))

                return None


            pocket = Pocket(

                pocket_id=f"pocket{i}",

                score=extract(
                    r"Score\s+:\s+([\d\.\-]+)"
                ),

                druggability=extract(
                    r"Druggability Score\s+:\s+([\d\.\-]+)"
                ),

                volume=extract(
                    r"Volume\s+:\s+([\d\.\-]+)"
                ),

                source_file=
                f"{pocket_folder}/pocket{i}_atm.pdb"

            )


            pockets.append(
                pocket
            )


        return pockets
