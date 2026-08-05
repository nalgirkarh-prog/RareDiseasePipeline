class LigandFilter:

    def evaluate(self, ligand):

        reasons = []

        if ligand.molecular_weight is not None and ligand.molecular_weight > 500:
            reasons.append("MW >500")

        if ligand.logp is not None and ligand.logp > 5:
            reasons.append("LogP >5")

        if ligand.hbd is not None and ligand.hbd > 5:
            reasons.append("HBD >5")

        if ligand.hba is not None and ligand.hba > 10:
            reasons.append("HBA >10")

        return {
            "accepted": len(reasons) == 0,
            "reasons": reasons
        }
