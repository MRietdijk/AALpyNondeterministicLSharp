from aalpy.automata.Lts import In, SuspensionAutomaton, Lts
from aalpy.oracles.PerfectKnowledgeLtsOracle import PerfectKnowledgeLtsOracle
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL
from aalpy.learning_algs.non_deterministic.LtsObservationTree import LtsObservationTree

class NonDeterministicLSharp():
    """
    The wrapper class for non-deterministic L#
    """

    def __init__(self, alphabet: set[In], sul: LtsAutomatonSUL, model_under_learning: Lts) -> None:
        """
        The constructor of the wrapper class for non-deterministic L#

        :param set[In] alphabet: Input alphabet.
        :param LtsAutomatonSUL sul: System under learning.
        :param Lts model_under_learning: The actual Labelled transition system model of the SUL.
        """
        self.oracle = PerfectKnowledgeLtsOracle(list(alphabet), sul , model_under_learning)
        self.observation_tree = LtsObservationTree(alphabet, sul, self.oracle)

    def run(self) -> SuspensionAutomaton:
        """
        The overall loop of Non-deterministic L#. Executes every rule of the observation tree.
        If a guard of a rule did fire, the loop continues to the next iteration.
        The loop will continue until it found a valid suspension automaton, which is identical to the SUL in the
        traces.

        :return SuspensionAutomaton: The trace equivalent suspension automaton of the SUL.
        """
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
        """
        Returns the statistics of the observation tree, which holds metrics like:
         - Number of tree states
         - Equivalence query calls
         - Completeness query calls
         - etc.
        :returns dict[str, float|int]: The statistics.
        """
        return self.observation_tree.get_current_stats()
