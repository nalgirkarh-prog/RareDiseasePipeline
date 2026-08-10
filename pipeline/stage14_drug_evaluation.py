from modules.drug_evaluator import DrugEvaluator


class DrugEvaluationStage:

    def __init__(self):

        self.evaluator = DrugEvaluator()

    def run(self, ranked_candidates):

        return self.evaluator.evaluate(
            ranked_candidates
        )
