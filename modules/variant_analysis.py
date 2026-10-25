import re


class VariantAnalyzer:


    def extract_protein_change(self, hgvs):

        """
        Extracts amino acid change from HGVS protein notation.

        Example:
        NP_004983.2:p.Arg133Cys

        Returns:
        Arg133Cys
        """

        if not hgvs:
            return None


        match = re.search(
            r"p\.([A-Za-z]+)(\d+)([A-Za-z*]+)",
            hgvs
        )


        if match:

            return match.group(0).replace(
                "p.",
                ""
            )


        return None



    def extract_residue(self, hgvs):

        """
        Extract residue number

        Example:
        p.Arg133Cys

        Returns:
        133
        """

        if not hgvs:
            return None


        match = re.search(
            r"(\d+)",
            hgvs
        )


        if match:

            return int(match.group(1))


        return None



    def map_to_sequence(
        self,
        residue,
        sequence
    ):


        if residue is None:
            return False


        if residue <= len(sequence):

            return True


        return False



    def predict_region(
        self,
        residue,
        gene_symbol: str = "MECP2"
    ):
        """
        Functional domain mapping for target proteins (DMD, MECP2, etc.).
        """
        if residue is None:
            return "unknown"

        gene = (gene_symbol or "").upper().strip()

        # Dystrophin (DMD) functional domain boundaries
        if gene == "DMD":
            if 1 <= residue <= 240:
                return "Actin-Binding Domain 1 (ABD1 / Calponin-Homology)"
            elif 241 <= residue <= 3040:
                return "Central Rod Domain (Spectrin Repeats R1-R24 / Hinges)"
            elif 3041 <= residue <= 3408:
                return "Cysteine-Rich Domain (CRD / beta-Dystroglycan Binding)"
            elif residue > 3408:
                return "C-Terminal Domain (CTD / Syntrophin-Dystrobrevin Binding)"
            return "N-terminal"

        # MECP2 functional domains (default fallback)
        if 90 <= residue <= 170:
            return "MBD"
        if 200 <= residue <= 310:
            return "TRD"
        if residue > 310:
            return "CTD"

        return "N-terminal"
