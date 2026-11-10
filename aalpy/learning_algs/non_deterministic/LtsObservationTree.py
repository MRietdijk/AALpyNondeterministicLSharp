from aalpy.automata.Lts import Label, Out, In, Lts, Trace, QUIESCENCE, SuspensionAutomaton, LtsState
from random import choice
from itertools import combinations
from aalpy.base.LtsOracle import LtsOracle
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL

from collections import deque
class LtsNode:
    """
    Single node of the observation tree for an LTS storing its labels
    to successors and its parent
    """

    _id_counter = 0

    def __init__(self, parent: 'LtsNode | None' = None, incomming_transition_label: Label | None = None, is_stable: bool = False, is_complete: bool = False) -> None:
        LtsNode._id_counter += 1
        self.id: int = LtsNode._id_counter
        self.successors: dict[Label, LtsNode] = {}
        self.parent: LtsNode | None = parent
        self.incomming_transition_label = incomming_transition_label
        self.is_complete:bool = is_complete
        self.is_stable = is_stable

    def extend_and_get(self, label: Label) -> 'LtsNode':
        if label not in self.successors:
            if label == QUIESCENCE:
                    child = LtsNode(parent=self, incomming_transition_label=label, is_stable=True, is_complete=True)
                    self.successors[label] = child
                    child.successors[label] = child
            else:
                child = LtsNode(parent=self, incomming_transition_label=label)
                self.successors[label] = child

        return self.successors[label]

    def is_enabled(self, label : Label) -> bool:
        return label in self.successors.keys()

    def get_nr_of_successors(self) -> int:
        nr_of_successors = 1
        for successor in self.successors.values():
            if successor is self:
                continue
            nr_of_successors += successor.get_nr_of_successors()
        return nr_of_successors

    def get_successor(self, label: Label) -> 'LtsNode | None':
        if label not in self.successors:
            return None
        return self.successors[label]

    def outputs(self) -> set[Out]:
        return {l for l in self.successors if isinstance(l, Out)}

    def inputs(self) -> set[In]:
        return {l for l in self.successors if isinstance(l, In)}

    def mark_complete(self) -> None:
        self.is_complete = True

    def get_witness(self, node: 'LtsNode') -> Trace | None:
        if node.is_complete and not self.outputs() <= node.outputs():
            witnesses = self.outputs() - node.outputs()
            return [choice(list(witnesses))]

        if self.is_complete and not node.outputs() <= self.outputs():
            witnesses = node.outputs() - self.outputs()
            return [choice(list(witnesses))]

        common_extensions = set(self.successors.keys()) & set(node.successors.keys())

        if self.is_stable and node.is_stable:
            common_extensions = common_extensions - {QUIESCENCE}

        for extension in common_extensions:
            child_node_1 = self.successors[extension]
            child_node_2 = node.successors[extension]

            partial_witness = child_node_1.get_witness(child_node_2)

            if partial_witness != None:
                partial_witness.insert(0, extension)
                return partial_witness

        return None


    def is_apart_from(self, node: 'LtsNode') -> bool:
        return self.get_witness(node) != None

    def __repr__(self):
        return f"LtsNode({self.id}, {list(self.successors)})"



class LtsObservationTree:

    def __init__(self, input_labels: set[In], sul: LtsAutomatonSUL, oracle: LtsOracle) -> None:
        self.sul = sul
        self.input_labels: set[In] = input_labels
        self.oracle = oracle
        self.root = LtsNode()
        self.basis = {self.root}
        
        self.statistics: dict[str, int|float] = {
            'promotion_rule_calls': 0,
            'extension_rule_calls': 0,
            'completion_rule_calls': 0,
            'identification_rule_calls': 0,
            'stable_rule_calls': 0,
            'conflict_processing_rule_calls': 0,
            'quiescent_reducible_rule_calls': 0,
            'equivalence_rule_calls': 0,
        }

        self.state_to_tree_node: dict[LtsState, LtsNode] = dict()

    def __get_nr_of_states(self) -> int:
        return self.root.get_nr_of_successors()

    def get_current_stats(self) -> dict[str, int|float]:
        new_statistics = self.statistics.copy()

        hypothesis = self.build_hypothesis()

        new_statistics['completeness_query_calls'] = self.oracle.num_comp_queries
        new_statistics['equivalence_query_calls'] = self.oracle.num_equiv_queries
        new_statistics['nr_of_tree_states'] = self.__get_nr_of_states()
        new_statistics['nr_of_hypothesis_states'] = len(hypothesis.states)

        return new_statistics


    def insert_observation(self, trace: Trace) -> None:
        current_node = self.root
        for label in trace:
            current_node = current_node.extend_and_get(label)

    def tree_after(self, trace: Trace) -> LtsNode | None:
        current_node = self.root
        for label in trace:
            successor_node = current_node.get_successor(label)
            if successor_node is None:
                return None
            current_node = successor_node

        return current_node

    def get_access_sequence(self, to_node: LtsNode) -> list[Label]:
        access_sequence = []
        current_node = to_node

        while current_node != self.root:
            if current_node is None:
                raise ValueError("'None' has no parent. Cannot retrieve the access sequence for 'None'")
            access_sequence.append(current_node.incomming_transition_label)
            current_node = current_node.parent

        access_sequence.reverse()
        return access_sequence

    def get_frontier(self) -> set[LtsNode]:
        frontier_nodes = set()
        for basis_node in self.basis:
            frontier_nodes = frontier_nodes | set(basis_node.successors.values())

        return frontier_nodes - self.basis

    def to_dot(self, highlight: set[LtsNode] | None = None) -> str:
        """
        Returns the observation tree as a Graphviz dot string. Nodes are named t_<id> after their node id,
        complete nodes are marked with ✓, basis nodes are bold, frontier nodes dashed and highlighted nodes filled.
        """
        highlight = highlight or set()
        frontier = self.get_frontier()

        names: dict[LtsNode, str] = {self.root: f"t_{self.root.id}"}
        order = [self.root]
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            for label in sorted(node.successors, key=str):
                child = node.successors[label]
                if child not in names:
                    names[child] = f"t_{child.id}"
                    order.append(child)
                    queue.append(child)

        def escape(text: str) -> str:
            return text.replace('\\', '\\\\').replace('"', '\\"')

        lines = ["digraph ObservationTree {", "    rankdir=TB;", "    node [shape=circle];"]
        for node in order:
            label = names[node] + (" ✓" if node.is_complete else "")
            styles = []
            if node in self.basis:
                styles.append("bold")
            elif node in frontier:
                styles.append("dashed")
            attributes = [f'label="{escape(label)}"']
            if node in highlight:
                styles.append("filled")
                attributes.append('fillcolor="lightblue"')
            if styles:
                attributes.append(f'style="{",".join(styles)}"')
            lines.append(f'    {names[node]} [{", ".join(attributes)}];')

        for node in order:
            for label in sorted(node.successors, key=str):
                child = node.successors[label]
                lines.append(f'    {names[node]} -> {names[child]} [label="{escape(str(label))}"];')

        lines.append("}")
        return "\n".join(lines) + "\n"

    def save_dot(self, path: str, highlight: set[LtsNode] | None = None) -> None:
        """Writes the dot representation of the observation tree to path."""
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.to_dot(highlight))

    def output_extension(self, node: LtsNode) -> bool:
        access_sequence = self.get_access_sequence(node)
        output_set = node.outputs()

        query_result = self.oracle.completeness_query(access_sequence, output_set)

        if query_result == None:
            node.mark_complete()
        else:
            node.extend_and_get(query_result)

        return query_result == None

    def do(self, node: LtsNode, witness: Trace) -> bool:
        if (len(witness) == 0):
            return True
        else:
            label = witness[0]
            rest = witness[1:]

            if (node.is_enabled(label)):
                next_node = node.get_successor(label)
                if not next_node:
                    raise ValueError(f"{label} is enabled in {node}, but has no successor")
                return self.do(next_node, rest)
            elif (isinstance(label, Out)):
                if node.is_complete:
                    return False

                while (not node.is_enabled(label)):
                    b = self.output_extension(node)
                    if (b):
                        return False

                next_node = node.get_successor(label)
                if not next_node:
                    raise ValueError(f"{label} is enabled in {node}, but has no successor")
                                
                return self.do(next_node, rest)
            else:
                new_node = node.extend_and_get(label)
                return self.do(new_node, rest)

    def promotion_rule(self) -> bool:
        frontier_nodes = self.get_frontier()
        fired = False

        for frontier_node in frontier_nodes:
            apartness_dict = dict.fromkeys(self.basis, False)
            for basis_node in apartness_dict:
                if basis_node.is_apart_from(frontier_node):
                    apartness_dict[basis_node] = True

            if all(apartness_dict.values()):
                self.basis.add(frontier_node)
                self.statistics['promotion_rule_calls'] += 1
                fired = True

        return fired



    def extension_rule(self) -> bool: 
        fired = False
        for basis_node in self.basis:
            inputs = basis_node.inputs()
            for i in self.input_labels - inputs:
                q = basis_node.extend_and_get(i)
                self.output_extension(q)
                self.statistics['extension_rule_calls'] += 1 
                fired = True

        return fired
                

    def completion_rule(self) -> bool:
        fired = False
        for basis_node in self.basis:
            if not basis_node.is_complete:
                b = False
                while not b:
                    b = self.output_extension(basis_node)
                
                self.statistics['completion_rule_calls'] += 1
                fired = True

        return fired
                
    def find_candidates(self, node: LtsNode) -> set[LtsNode]:
        candidates = set()
        for basis_node in self.basis:
            if not node.is_apart_from(basis_node):
                candidates.add(basis_node)

        return candidates

    def identification_rule(self) -> bool:
        fired = False
        for frontier_node in self.get_frontier():
            candidates = self.find_candidates(frontier_node)

            while len(candidates) > 1:
                r1, r2 = next(combinations(candidates, 2))
                witness = r1.get_witness(r2)
                if witness is None:
                    raise AssertionError(f"{r1} and {r2} are in the basis, but are not apart from each other")

                self.do(frontier_node, witness)
                self.statistics['identification_rule_calls'] += 1
                fired = True

                candidates = self.find_candidates(frontier_node)

        return fired

    def find_identifier(self, node: LtsNode) -> LtsNode | None:
        candidates = self.find_candidates(node)
        if len(candidates) == 1:
            return candidates.pop()
        else:
            return None

    def stable_rule(self) -> bool:
        fired = False
        for q in self.basis:
            r = q.get_successor(QUIESCENCE)
            if r is None:
                continue

            q_prime = self.find_identifier(r)

            if q_prime is None:
                continue

            r_prime = q_prime.get_successor(QUIESCENCE)

            if r_prime is None:
                continue

            witness = q_prime.get_witness(r_prime)

            if witness is None:
                continue

            self.do(r, witness)
            self.statistics['stable_rule_calls'] += 1
            fired = True

        return fired

    def build_hypothesis(self) -> SuspensionAutomaton:
        tree_node_to_state: dict[LtsNode, LtsState] = dict()

        for node in self.basis:
            tree_node_to_state[node] = LtsState(f"s{node.id}")

        for basis_node, state in tree_node_to_state.items():
            for label in self.input_labels | basis_node.outputs():
                successor = basis_node.get_successor(label)

                if successor is None:
                    raise AssertionError(f"Not all basis states are input-enabled: {label} is not enabled in {basis_node.id}")

                if successor not in self.basis:
                    identifier = self.find_identifier(successor)
                    if identifier is None:
                        raise AssertionError(f"Frontier node {successor.id} is not identified with a unique basis node")
                    successor = identifier

                state.transitions[label] = [tree_node_to_state[successor]]

        for node, state in tree_node_to_state.items():
            self.state_to_tree_node[state] = node

        return SuspensionAutomaton(tree_node_to_state[self.root], list(tree_node_to_state.values()))

    def __prefix_to_frontier(self, trace: Trace):
        prefix = []
        current_node = self.root
        for label in trace:
            if current_node is None or current_node not in self.basis:
                break

            prefix.append(label)
            current_node = current_node.get_successor(label)

        return prefix

    def __find_node_state_witness(self, node: LtsNode, state: LtsState) -> Trace | None:
        queue = deque([(node, state, [])])

        visited = {(node, state)}

        while queue:
            r, q, trace = queue.popleft()

            additional_tree_outputs = r.outputs() - q.outputs()
            additional_hyp_outputs = q.outputs() - r.outputs()

            if additional_tree_outputs:
                return trace + [additional_tree_outputs.pop()]

            if r.is_complete and additional_hyp_outputs:
                return trace + [additional_hyp_outputs.pop()]

            for label, child in r.successors.items():
                if label not in q.transitions:
                    continue
                pair = (child, q.transitions[label][0])
                if pair not in visited:
                    visited.add(pair)
                    queue.append((*pair, trace + [label]))

        return None


    def conflict_processing_rule(self, hypothesis: SuspensionAutomaton) -> bool:
        frontier = self.get_frontier()
        queue = deque(frontier)
        seen = set(frontier)

        while queue:
            r = queue.popleft()
            for child in r.successors.values():
                if child not in seen:
                    seen.add(child)
                    queue.append(child)

            if r in frontier:
                continue

            access_r = self.get_access_sequence(r)
            q = hypothesis.suspension_automaton_after(hypothesis.initial_state, access_r)

            if q is None:
                continue

            sigma = self.__find_node_state_witness(r, q)

            if sigma is None:
                continue

            prefix = self.__prefix_to_frontier(access_r)

            r_prime_access = access_r[:len(prefix)]
            rho = access_r[len(prefix):]

            q_prime_state = hypothesis.suspension_automaton_after(hypothesis.initial_state, r_prime_access)
            if q_prime_state is None:
                continue

            q_prime = self.state_to_tree_node[q_prime_state]
            self.do(q_prime, rho + sigma)
            self.statistics['conflict_processing_rule_calls'] += 1
            return True

        return False



    def __shortest_trace_difference(self, q_prime: LtsState, q: LtsState) -> Trace | None:
        queue = deque([(q_prime, q, [])])
        visited = {(q_prime, q)}

        while queue:
            p_prime, p, trace = queue.popleft()
            for label, targets in p_prime.transitions.items():
                if label not in p.transitions:
                    return trace + [label]
                pair = (targets[0], p.transitions[label][0])
                if pair not in visited:
                    visited.add(pair)
                    queue.append((*pair, trace + [label]))

        return None

    def add_trace(self, state: LtsNode, trace: Trace):
        current_state = state
        for symbol in trace:
            current_state = current_state.extend_and_get(symbol)

    def quiescent_reducible_rule(self, hypothesis: SuspensionAutomaton) -> bool:
        for q in hypothesis.states:
            if QUIESCENCE not in q.outputs():
                continue

            r = hypothesis.suspension_automaton_after(q, [QUIESCENCE])

            if r is None:
                continue

            sigma = self.__shortest_trace_difference(r, q)

            if sigma is None:
                continue

            q_node = self.state_to_tree_node[q]
            q_prime = q_node.get_successor(QUIESCENCE)

            if q_prime is None:
                raise AssertionError(f"State {q} is quiescent in the hypothesis, but {q_node} does not allow a δ-transition in the tree.")

            if (self.do(q_prime, sigma)):
                self.add_trace(q_node, sigma)

            self.statistics['quiescent_reducible_rule_calls'] += 1
            return True

        return False

    def equivalence_rule(self, hypothesis: SuspensionAutomaton) -> bool:
        self.statistics['equivalence_rule_calls'] += 1
        counter_example = self.oracle.find_cex(hypothesis)

        if counter_example is None:
            return True

        counter_example_state = hypothesis.suspension_automaton_after(hypothesis.initial_state, counter_example)

        if counter_example_state:
            self.do(self.root, counter_example)
        else:
            self.insert_observation(counter_example)

        return False