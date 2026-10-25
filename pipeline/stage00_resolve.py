from clients.disease.resolver import DiseaseResolverEngine


class DiseaseResolver:

    def __init__(self):
        self.engine = DiseaseResolverEngine()

    def run(self, disease):
        # Direct check for explicit gene symbol (Option A: Bypass Resolver)
        explicit_gene = getattr(disease, "gene_symbol", None)
        if not explicit_gene and isinstance(disease, dict):
            explicit_gene = disease.get("gene_symbol")

        if explicit_gene:
            gene = str(explicit_gene).strip().upper()
            print(f"\n▶ Target gene explicitly specified: {gene}")
            return gene

        print(f"\nResolving {disease}")
        gene = self.engine.resolve(disease)
        print(f"Gene: {gene}")
        return gene
