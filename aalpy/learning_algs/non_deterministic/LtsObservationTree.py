from aalpy.automata.Lts import Label, Out, In, Lts, Trace
from random import choice
from itertools import combinations

class LtsNode:
    """
    Single node of the observation tree for an LTS storing its labels
    to successors and its parent
    """

    _id_counter = 0

    def __init__(self, parent: 'LtsNode | None' = None, incomming_transition_label: Label | None = None) -> None:
        LtsNode._id_counter += 1
        self.id: int = LtsNode._id_counter
        self.successors: dict[Label, LtsNode] = {}
        self.parent: LtsNode | None = parent
        self.incomming_transition_label = incomming_transition_label
        self.is_complete:bool = False

    def extend_and_get(self, label: Label) -> 'LtsNode':
        if label not in self.successors:
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


class LtsObservationTree:

    def __init__(self, input_labels: set[In], sul: Lts) -> None:
        self.sul: Lts = sul
        self.input_labels: set[In] = input_labels
        
        self.root = LtsNode()
        self.basis = {self.root}

        self.states_dict = dict()

        self.state_to_tree_node = dict()

    def insert_observation(self, trace: Trace) -> None:
        current_node = self.root
        for label in trace:
            current_node = current_node.extend_and_get(label)

    def get_successor(self, trace: Trace) -> LtsNode | None:
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

    def process_example(self, example: Trace, node: LtsNode) -> bool:
        current_node = node

        for label in example:
            if current_node.is_enabled(label):
                current_node = current_node.successors[label]
                continue
            elif isinstance(label, Out):
                if current_node.is_complete:
                    return False
                b = False
                o = None
                while label != o and not b:
                    pass
                    # TODO: Do equivalence queries on `current_node`
                if b:
                    current_node.mark_complete()
                    return False
                current_node = current_node.successors[label]
            else:
                current_node = current_node.extend_and_get(label)
        
        return True

    def promotion_rule(self) -> None:
        frontier_nodes = self.get_frontier()

        for frontier_node in frontier_nodes:
            apartness_dict = dict.fromkeys(self.basis, False)
            for basis_node in apartness_dict:
                if basis_node.is_apart_from(frontier_node):
                    apartness_dict[basis_node] = True

            if all(apartness_dict.values()):
                self.basis.add(frontier_node)

    def extension_rule(self) -> None:  
        for basis_node in self.basis:
            inputs = basis_node.inputs()
            for i in self.input_labels - inputs:
                new_node = basis_node.extend_and_get(i)
                # TODO: do a completeness query on `new_node`

    def completion_rule(self) -> None:
        for basis_node in self.basis:
            if not basis_node.is_complete:
                pass
                # TODO: Call completeness query on `basis_node`

    def find_candidates(self, node: LtsNode) -> set[LtsNode]:
        candidates = set()
        for basis_node in self.basis:
            if not basis_node.is_apart_from(basis_node):
                candidates.add(basis_node)

        return candidates

    def identification_rule(self) -> None:
        for frontier_node in self.get_frontier():
            candidates = self.find_candidates(frontier_node)

            for r1, r2 in combinations(candidates, 2):
                witness = r1.get_witness(r2)
                # TODO: Process example on `witness` and `frontier_node`
