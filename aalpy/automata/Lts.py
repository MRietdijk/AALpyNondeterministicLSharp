from aalpy.base import AutomatonState, Automaton
from typing import Generic, TypeAlias
from aalpy.base.Automaton import InputType, OutputType
from collections.abc import Hashable
from dataclasses import dataclass

from random import choice


@dataclass(frozen=True)
class In(Generic[InputType]):
    """Input label, written as ?sym."""
    sym: InputType

    def __str__(self) -> str:
        return f"?{self.sym}"


@dataclass(frozen=True)
class Out(Generic[OutputType]):
    """Output label, written as !sym."""
    sym: OutputType

    def __str__(self) -> str:
        return f"!{self.sym}"


@dataclass(frozen=True)
class Quiescence:
    """Symbol of the quiescence output δ: observed when a state enables no output."""

    def __str__(self) -> str:
        return QUIESCENCE_SYMBOL


# Output label for quiescence, written as !δ. It is never stored as a transition: it is an implicit self-loop
# on every state without outputs.
QUIESCENCE: Out[Quiescence] = Out(Quiescence())

# Symbol used for QUIESCENCE in state setup dictionaries.
QUIESCENCE_SYMBOL = "δ"


@dataclass(frozen=True)
class Tau:
    """Label of an internal, unobservable transition τ."""

    def __str__(self) -> str:
        return TAU_SYMBOL


# Label of internal transitions. It is never observed: traces only contain inputs and outputs.
TAU = Tau()

# Symbol used for TAU in state setup dictionaries, written as the key (TAU_SYMBOL, None).
TAU_SYMBOL = "τ"

# A label is an input In(sym), an output Out(sym) or the internal label TAU.
Label: TypeAlias = In[InputType] | Out[OutputType] | Tau
Trace: TypeAlias = list[Label]

class LtsState(AutomatonState, Generic[InputType, OutputType]):
    """
    Single state of an input-output labelled transition system. The transitions are encoded in a dictionary from a label to a 
    list of states.
    """

    def __init__(self, state_id: Hashable) -> None:
        super().__init__(state_id)

        self.transitions: dict[Label, list[LtsState[InputType, OutputType]]] = {}

    def inputs(self) -> set[In[InputType]]:
        return {label for label in self.transitions if isinstance(label, In)}

    def outputs(self) -> set[Out[OutputType]]:
        return {label for label in self.transitions if isinstance(label, Out)}

    def successor_states(self, label: Label) -> list['LtsState[InputType, OutputType]']:
        return self.transitions.get(label, [])

    def add_input(self, inp: InputType, target: 'LtsState[InputType, OutputType]') -> None:
        self.transitions.setdefault(In(inp), []).append(target)

    def add_output(self, out: OutputType, target: 'LtsState[InputType, OutputType]') -> None:
        self.transitions.setdefault(Out(out), []).append(target)

    def add_tau(self, target: 'LtsState[InputType, OutputType]') -> None:
        self.transitions.setdefault(TAU, []).append(target)

    def is_quiescent(self) -> bool:
        """A state is quiescent if it enables no output and no internal transition."""
        return not self.outputs() and TAU not in self.transitions

    
class Lts(Automaton[LtsState[InputType, OutputType]]):
    """
    Input-output Labelled Transition System
    """

    def __init__(self, initial_state: LtsState[InputType, OutputType], states: list[LtsState[InputType, OutputType]]) -> None:
        super().__init__(initial_state, states)

    def step(self, letter: In[InputType] | None) -> Out[OutputType] | Out[Quiescence] | None:
        """
        If letter is an input label: take that input transition (non-deterministically) and return None.
        If letter is None: let the system produce an output. Picks one enabled output at random,
        moves to one of the successors of that enabled output and returns its label;
        returns QUIESCENCE and stays in a quiescent state if no output is enabled.
        Internal transitions are taken silently, before and after the input or output.
        """
        if letter is not None:
            targets = list(self.after_states({self.current_state}, [letter]))
            if not targets:
                raise ValueError(f"input {letter} is not enabled in {self.current_state.state_id}")
            self.current_state = choice(targets)
            return None

        output = choice(list(self.out({self.current_state})))

        self.current_state = choice(list(self.after_states({self.current_state}, [output])))

        return output

    def _enabled_outputs(self, state: LtsState[InputType, OutputType]) -> set[Out[OutputType] | Out[Quiescence]]:
        """
        Returns the outputs enabled in a state. Quiescence is implicit: a quiescent state enables only QUIESCENCE.
        A state with only internal transitions enables no output itself; its τ-successors do.
        """
        if state.is_quiescent():
            return {QUIESCENCE}
        return set(state.outputs())

    def _successors(self, state: LtsState[InputType, OutputType], label: Label) -> list[LtsState[InputType, OutputType]]:
        """
        Returns the successors of a state for a label. QUIESCENCE is an implicit self-loop on quiescent states and leads
        nowhere from other states.
        """
        if label == QUIESCENCE:
            return [state] if state.is_quiescent() else []
        return state.successor_states(label)

    def tau_closure(self, states: set[LtsState[InputType, OutputType]]) -> set[LtsState[InputType, OutputType]]:
        """
        Returns the states reachable from the given states with zero or more internal transitions.
        """
        closure = set(states)
        stack = list(states)
        while stack:
            for successor in stack.pop().successor_states(TAU):
                if successor not in closure:
                    closure.add(successor)
                    stack.append(successor)
        return closure

    def get_input_alphabet(self) -> list[In[InputType]]:
        """
        Returns the input alphabet, in order of first occurrence (stable across runs).
        """
        alphabet = list()
        for s in self.states:
            for label in s.transitions:
                if isinstance(label, In) and label not in alphabet:
                    alphabet.append(label)
        return alphabet

    def is_input_complete(self) -> bool:
        """
        Checks that every input is enabled in every state, possibly after internal transitions.
        """
        input_alphabet = set(self.get_input_alphabet())
        return all(set().union(*(q.inputs() for q in self.tau_closure({s}))) == input_alphabet for s in self.states)

    def get_output_alphabet(self) -> list[Out[OutputType]]:
        """
        Returns the output alphabet, in order of first occurrence (stable across runs).
        """
        alphabet = list()
        for s in self.states:
            for label in s.transitions:
                if isinstance(label, Out) and label not in alphabet:
                    alphabet.append(label)
        return alphabet

    def out(self, states: set[LtsState[InputType, OutputType]]) -> set[Out[OutputType] | Out[Quiescence]]:
        """
        Returns the enabled outputs for a set of states, including QUIESCENCE if any state is quiescent.
        States reachable with internal transitions are included.
        """
        outputs = set()

        for state in self.tau_closure(states):
            outputs |= self._enabled_outputs(state)

        return outputs

    def after_states(self, states: set[LtsState], trace: Trace) -> set[LtsState]:
        """
        Given a set of states in the LTS and a trace, we return the set of states were we can end up from these states
        after sigma, taking internal transitions before and after every label. The result is closed under τ.
        """
        current = self.tau_closure(states)
        for label in trace:
            current = self.tau_closure({successor for state in current for successor in self._successors(state, label)})

        return current

    def after(self, state: LtsState[InputType, OutputType], trace: Trace) -> set[LtsState[InputType, OutputType]]:
        """
        Given a state in the LTS and a trace, we return the set of states were
        we can end up from the given state after sigma
        """
        return self.after_states({state}, trace)

    def to_state_setup(self) -> dict:
        """
        Converts the LTS to a state setup dictionary. The initial state is the first entry.

        :return dict: Map from state_id to a dict mapping (label_type_value, symbol) to a list of target state_ids,
            e.g. {'s0': {('?', 'coin'): ['s1']}, 's1': {('!', 'coffee'): ['s0'], ('τ', None): ['s0']}}.
        """
        state_setup_dict = {}

        # ensure initial state is first in the dict
        ordered_states = [self.initial_state] + [s for s in self.states if s != self.initial_state]

        for s in ordered_states:
            state_setup_dict[s.state_id] = {Lts._setup_key(label): [target.state_id for target in targets]
                                            for label, targets in s.transitions.items()}

        return state_setup_dict

    @staticmethod
    def _setup_key(label: Label) -> tuple:
        """
        Returns the state setup key of a label: ('?', sym), ('!', sym), ('!', QUIESCENCE_SYMBOL) or (TAU_SYMBOL, None).
        """
        if label == TAU:
            return TAU_SYMBOL, None
        if label == QUIESCENCE:
            return '!', QUIESCENCE_SYMBOL
        return '?' if isinstance(label, In) else '!', label.sym

    @staticmethod
    def _states_from_setup(state_setup: dict) -> tuple[LtsState, list[LtsState]]:
        """
        Builds the states of a state setup dictionary, returning the initial state and all states.
        The output symbol QUIESCENCE_SYMBOL is mapped to QUIESCENCE and the kind TAU_SYMBOL to TAU.
        """
        states_map = {key: LtsState(key) for key in state_setup.keys()}

        for key, transitions in state_setup.items():
            source = states_map[key]
            for (kind, sym), targets in transitions.items():
                for target in targets:
                    if kind == TAU_SYMBOL:
                        label = TAU
                    elif kind == '?':
                        label = In(sym)
                    else:
                        label = QUIESCENCE if sym == QUIESCENCE_SYMBOL else Out(sym)
                    source.transitions.setdefault(label, []).append(states_map[target])

        initial_state = states_map[list(state_setup.keys())[0]]
        return initial_state, list(states_map.values())

    @staticmethod
    def from_state_setup(state_setup: dict, **kwargs) -> 'Lts':
        """
        Creates an LTS from a state setup dictionary. The first state in the state setup is the initial state.

        :param dict state_setup: Map from state_id to a dict mapping (label_type_value, symbol) to a list of
            target state_ids, where label_type_value is '?' for inputs and '!' for outputs. Internal transitions
            are written as (TAU_SYMBOL, None).
        :return Lts: The constructed LTS.
        """
        return Lts(*Lts._states_from_setup(state_setup))


class SuspensionAutomaton(Lts):
    """
    Suspension automaton: an LTS where quiescence is an explicit output. A δ transition is stored like any other
    output transition and may lead to a different state. Hypotheses of IOTS learning are suspension automata.
    """

    def _enabled_outputs(self, state: LtsState[InputType, OutputType]) -> set[Out[OutputType] | Out[Quiescence]]:
        """
        Returns the outputs enabled in a state, where QUIESCENCE is only enabled through an explicit transition.
        """
        return set(state.outputs())

    def _successors(self, state: LtsState[InputType, OutputType], label: Label) -> list[LtsState[InputType, OutputType]]:
        return state.successor_states(label)

    def validate(self) -> None:
        """
        Checks that every state enables at least one output (QUIESCENCE counts) and that the automaton is deterministic,
        so in particular has no internal transitions. Raises a ValueError otherwise.
        """
        for state in self.states:
            if TAU in state.transitions:
                raise ValueError(f"state {state.state_id} has an internal transition {TAU}")
            if not state.outputs():
                raise ValueError(f"state {state.state_id} enables no output, not even {QUIESCENCE}")
            for label, targets in state.transitions.items():
                if len(targets) > 1:
                    raise ValueError(f"state {state.state_id} is non-deterministic on {label}")

    @staticmethod
    def from_state_setup(state_setup: dict, **kwargs) -> 'SuspensionAutomaton':
        """
        Creates a suspension automaton from a state setup dictionary. The first state in the state setup is the
        initial state. Quiescence transitions are written as ('!', QUIESCENCE_SYMBOL).

        :param dict state_setup: Map from state_id to a dict mapping (label_type_value, symbol) to a list of
            target state_ids, where label_type_value is '?' for inputs and '!' for outputs.
        :return SuspensionAutomaton: The constructed suspension automaton.
        """
        return SuspensionAutomaton(*Lts._states_from_setup(state_setup))