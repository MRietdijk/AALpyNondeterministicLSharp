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

        # because we otherwise will not terminate while searching for a counter example.
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

        self.state_to_tree_node: dict[LtsState, LtsNode] = dict()

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

        return frontier_nodes

    def check_complete_output(self, node: LtsNode) -> bool:
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
                    b = self.check_complete_output(node)
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
                fired = True

        return fired


    def extension_rule(self) -> bool:  
        fired = False
        for basis_node in self.basis:
            inputs = basis_node.inputs()
            for i in self.input_labels - inputs:
                basis_node.extend_and_get(i)
                fired = True

        return fired
                

    def completion_rule(self) -> bool:
        fired = False
        for basis_node in self.basis:
            if not basis_node.is_complete:
                self.check_complete_output(basis_node)
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

            for r1, r2 in combinations(candidates, 2):
                witness = r1.get_witness(r2)
                if witness == None:
                    raise AssertionError(f"{r1} and {r2} are in the basis, but are not apart from each other")

                self.do(frontier_node, witness)
                fired = True

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

                state.transitions[label] = [tree_node_to_state[successor]]

        for node, state in tree_node_to_state.items():
            self.state_to_tree_node[state] = node

        return SuspensionAutomaton(tree_node_to_state[self.root], list(tree_node_to_state.values()))

    def __prefix_to_frontier(self, trace: Trace):
        prefix = []
        current_node = self.root
        frontier = self.get_frontier()
        for label in trace:
            if current_node in frontier or current_node is None:
                break

            current_node = current_node.get_successor(label)

        return prefix

    def process_conflict(self, hypothesis: SuspensionAutomaton, trace: Trace, conflict: Trace):
        r = self.tree_after(trace)

        if r in self.basis | self.get_frontier():
            return

        rho = self.__prefix_to_frontier(trace)

        h = (len(rho) + len(trace)) // 2

        sigma_1 = trace[:h]
        sigma_2 = trace[h:]

        q_prime_hypothesis = hypothesis.after(hypothesis.initial_state, sigma_1)
        q_prime_hypothesis = q_prime_hypothesis.pop()
        q_prime_tree = self.state_to_tree_node[q_prime_hypothesis]
        r_prime = self.tree_after(sigma_1)

        if r_prime is None:
            raise AssertionError("process_conflict: sigma_1 is not defined")

        access_q_prime = self.get_access_sequence(q_prime_tree)

        self.do(self.root, access_q_prime + sigma_2 + conflict)

        witness_q_prime_r_prime = q_prime_tree.get_witness(r_prime)
        if witness_q_prime_r_prime:
            self.process_conflict(hypothesis, sigma_1, witness_q_prime_r_prime)
        else:
            self.process_conflict(hypothesis, access_q_prime + sigma_2, conflict)

    def process_counter_example(self, hypothesis: SuspensionAutomaton, counter_example: Trace):
        self.do(self.root, counter_example)
        new_trace = []
        conflict: Label | None = None
        if (hypothesis.after(hypothesis.initial_state, counter_example)):
            new_trace = counter_example[:-1]
            conflict = counter_example[-1]
        else:
            state_hypothesis = hypothesis.initial_state
            for label in counter_example:
                if not hypothesis.after(state_hypothesis, [label]):
                    conflict = label
                    break
                new_trace.append(label)

        if isinstance(conflict, In):
            raise AssertionError("Hypothesis is not input-enabled")

        if conflict is None:
            raise AssertionError("No conflict found in counter example")
                            
        self.process_conflict(hypothesis, new_trace, [conflict])

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

    def quiescent_reducible_rule(self, hypothesis: SuspensionAutomaton) -> bool:
        fired = False
        for q in hypothesis.states:
            if QUIESCENCE not in q.outputs():
                continue

            q_prime = q.transitions[QUIESCENCE][0]
            sigma = self.__shortest_trace_difference(q_prime, q)
            
            if sigma is None:
                continue

            q_node = self.state_to_tree_node[q]

            access_q = self.get_access_sequence(q_node)

            if self.do(q_node, sigma):
                self.process_counter_example(hypothesis, access_q + sigma)
            else:
                self.process_counter_example(hypothesis, access_q + [QUIESCENCE] + sigma)
            fired = True

        return fired

    def equivalence_rule(self, hypothesis: SuspensionAutomaton) -> bool:
        counter_example = self.oracle.find_cex(hypothesis)

        if counter_example is None:
            return True

        self.process_counter_example(hypothesis, counter_example)
        return False