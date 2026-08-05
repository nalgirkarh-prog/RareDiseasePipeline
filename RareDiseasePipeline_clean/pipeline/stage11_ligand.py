from modules.ligand_discovery import LigandDiscovery
from modules.ligand_filter import LigandFilter


class LigandScreeningStage:

    def __init__(self):

        self.discovery = LigandDiscovery()

        self.filter = LigandFilter()

    def run(
        self,
        protein,
        pockets,
        interactions
    ):

        print("\nLigand discovery started...")

        ligands = self.discovery.discover(
            interactions=interactions
        )

        print(f"Discovered {len(ligands)} ligands")

        print(
            f"Prepared {len(ligands)} candidate ligands for docking (3 sets of 10 max)"
        )

        return ligands

