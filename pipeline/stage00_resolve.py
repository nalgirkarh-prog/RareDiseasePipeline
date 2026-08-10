from clients.disease.resolver import DiseaseResolverEngine


class DiseaseResolver:

    def __init__(self):

        self.engine = DiseaseResolverEngine()

    def run(self, disease):

        print(f"\nResolving {disease}")

        gene = self.engine.resolve(disease)

        print(f"Gene: {gene}")

        return gene
