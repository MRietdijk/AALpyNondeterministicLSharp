from aalpy.automata.Lts import In, SuspensionAutomaton, Lts
from aalpy.oracles.PerfectKnowledgeLtsOracle import PerfectKnowledgeLtsOracle
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL
from aalpy.learning_algs.non_deterministic.LtsObservationTree import LtsObservationTree

class NonDeterministicLSharp():

    def __init__(self, alphabet: set[In], sul: LtsAutomatonSUL, model_under_learning: Lts) -> None:
        self.oracle = PerfectKnowledgeLtsOracle(list(alphabet), sul , model_under_learning)
        self.observation_tree = LtsObservationTree(alphabet, sul, self.oracle)

    def run(self) -> SuspensionAutomaton:
        while True:
                if self.observation_tree.promotion_rule():
                    continue
                elif self.observation_tree.extension_rule():
                    continue
                elif self.observation_tree.completion_rule():
                    continue
                elif self.observation_tree.identification_rule():
                    continue
                elif self.observation_tree.stable_rule():
                    continue
                else:
                    hypothesis = self.observation_tree.build_hypothesis()
        
                    if self.observation_tree.conflict_processing_rule(hypothesis):
                        continue
                    elif self.observation_tree.quiescent_reducible_rule(hypothesis):
                        continue
                    else:
                        b = self.observation_tree.equivalence_rule(hypothesis)
                        if b:
                            return hypothesis

    def get_statistics(self) -> dict[str, float|int]:
        return self.observation_tree.get_current_stats()
