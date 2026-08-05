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
        residue
    ):

        """
        MECP2 functional domains
        """

        if residue is None:
            return "unknown"


        # Methyl CpG Binding Domain
        if 90 <= residue <= 170:

            return "MBD"


        # Transcriptional repression domain
        if 200 <= residue <= 310:

            return "TRD"


        # C-terminal domain
        if residue > 310:

            return "CTD"


        return "N-terminal"
