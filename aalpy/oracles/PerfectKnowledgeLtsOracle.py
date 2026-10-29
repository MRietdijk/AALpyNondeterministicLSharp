from aalpy.automata.Lts import In, Lts, Out, Trace
from aalpy.base.LtsOracle import LtsOracle
from aalpy.base.LtsSUL import LtsSUL
from collections import deque
from random import choice

class PerfectKnowledgeLtsOracle(LtsOracle):

    def __init__(self, input_alphabet: list[In], sul: LtsSUL, model_under_learning: Lts) -> None:
        super().__init__(input_alphabet, sul)
        self.model_under_learning = model_under_learning

    def completeness_query(self, trace: list[In | Out], outputs: set[Out]) -> Out | None:
        model = self.model_under_learning
        self.num_queries += 1
        states = model.after(model.initial_state, trace)
        if not states:
            raise ValueError(f"{trace} is not a trace of the model")
        real_output_set = model.out(states)
        if (outputs - real_output_set):
            raise ValueError(f"{outputs - real_output_set} is/are not members of the model after {trace}")
        elif (real_output_set == outputs):
            return None

        return choice(list(real_output_set - outputs))

    def find_cex(self, hypothesis: Lts) -> Trace | None:
        """
        Checks suspension-trace equivalence between the hypothesis (a suspension automaton) and the model under learning
        with a breadth-first search over pairs of state sets, so the returned counterexample is a shortest one.

        :return Trace | None: A trace ending in a label that one system enables after the prefix and the other does not,
            None if the hypothesis and model have the same suspension traces.
        """
        model = self.model_under_learning
        self.num_queries += 1

        start = (frozenset({hypothesis.initial_state}), frozenset({model.initial_state}))
        visited = {start}
        queue: deque[tuple[frozenset, frozenset, Trace]] = deque([(start[0], start[1], [])])

        while queue:
            hyp_states, model_states, trace = queue.popleft()
            self.num_steps += 1

            hyp_outputs = hypothesis.out(set(hyp_states))
            model_outputs = model.out(set(model_states))
            if hyp_outputs != model_outputs:
                return trace + [min(hyp_outputs ^ model_outputs, key=str)]

            hyp_inputs = set().union(*(s.inputs() for s in hyp_states))
            model_inputs = set().union(*(s.inputs() for s in model_states))
            if hyp_inputs != model_inputs:
                return trace + [min(hyp_inputs ^ model_inputs, key=str)]

            for label in sorted(hyp_inputs | hyp_outputs, key=str):
                successors = (frozenset(hypothesis.after_states(set(hyp_states), [label])),
                              frozenset(model.after_states(set(model_states), [label])))
                if successors not in visited:
                    visited.add(successors)
                    queue.append((successors[0], successors[1], trace + [label]))

        return None
        
