from modules.solution_builder import SolutionBuilder


class SolutionBuilderStage:

    def __init__(self):
        self.builder = SolutionBuilder()

    def run(self, context):

        print("\n==============================")
        print("STAGE 15 : Solution Builder")
        print("==============================")

        return self.builder.build(context)
