from aalpy.automata.Lts import In, SuspensionAutomaton, Lts
from aalpy.oracles.PerfectKnowledgeLtsOracle import PerfectKnowledgeLtsOracle
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL
from aalpy.learning_algs.non_deterministic.LtsObservationTree import LtsObservationTree

def run_non_deterministic_l_sharp(alphabet: set[In], sul: LtsAutomatonSUL, model_under_learning: Lts) -> SuspensionAutomaton:
    oracle = PerfectKnowledgeLtsOracle(list(alphabet), sul, model_under_learning)
    observation_tree = LtsObservationTree(alphabet, sul, oracle)
    
    while True:
        if observation_tree.promotion_rule():
            continue
        elif observation_tree.extension_rule():
            continue
        elif observation_tree.completion_rule():
            continue
        elif observation_tree.identification_rule():
            continue
        elif observation_tree.stable_rule():
            continue
        else:
            hypothesis = observation_tree.build_hypothesis()

            if observation_tree.quiescent_reducible_rule(hypothesis):
                continue
            else:
                b = observation_tree.equivalence_rule(hypothesis)
                if b:
                    return hypothesis