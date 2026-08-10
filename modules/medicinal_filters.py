from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import Crippen
from rdkit.Chem import Lipinski
from rdkit.Chem import QED


class MedicinalFilters:

    def evaluate(self, smiles):

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return None

        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        hbd = Lipinski.NumHDonors(mol)
        hba = Lipinski.NumHAcceptors(mol)
        rot = Lipinski.NumRotatableBonds(mol)
        qed = QED.qed(mol)

        return {

            "mw": mw,
            "logp": logp,
            "tpsa": tpsa,
            "hbd": hbd,
            "hba": hba,
            "rotatable_bonds": rot,
            "qed": qed,

            "lipinski": self.lipinski(
                mw,
                logp,
                hbd,
                hba
            ),

            "veber": self.veber(
                rot,
                tpsa
            ),

            "ghose": self.ghose(
                mw,
                logp
            ),

            "egan": self.egan(
                logp,
                tpsa
            ),

            "muegge": self.muegge(
                mw,
                logp,
                tpsa,
                hba,
                hbd,
                rot
            ),

            "hbond": self.hbond_filter(
                hbd,
                hba
            )

        }

    def hbond_filter(self, hbd, hba):

        return (
            hbd is not None and
            hba is not None and
            0 <= hbd <= 5 and
            0 <= hba <= 10 and
            1 <= (hbd + hba) <= 12
        )

    def lipinski(self, mw, logp, hbd, hba):


        return (
            mw <= 500 and
            logp <= 5 and
            hbd <= 5 and
            hba <= 10
        )

    def veber(self, rot, tpsa):

        return (
            rot <= 10 and
            tpsa <= 140
        )

    def ghose(self, mw, logp):

        return (
            160 <= mw <= 480 and
            -0.4 <= logp <= 5.6
        )

    def egan(self, logp, tpsa):

        return (
            logp <= 5.88 and
            tpsa <= 131
        )

    def muegge(
        self,
        mw,
        logp,
        tpsa,
        hba,
        hbd,
        rot
    ):

        return (
            200 <= mw <= 600 and
            -2 <= logp <= 5 and
            tpsa <= 150 and
            hba <= 10 and
            hbd <= 5 and
            rot <= 15
        )
