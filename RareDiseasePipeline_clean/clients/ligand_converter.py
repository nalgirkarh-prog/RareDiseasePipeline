from rdkit import Chem
from rdkit.Chem import AllChem


class LigandConverter:


    def smiles_to_sdf(
        self,
        smiles,
        filename
    ):


        mol = Chem.MolFromSmiles(
            smiles
        )


        mol = Chem.AddHs(
            mol
        )


        AllChem.EmbedMolecule(
            mol
        )


        AllChem.MMFFOptimizeMolecule(
            mol
        )


        writer = Chem.SDWriter(
            filename
        )


        writer.write(
            mol
        )


        writer.close()


        return filename
