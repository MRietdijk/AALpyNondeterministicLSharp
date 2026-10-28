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

# A label is either an input In(sym) or an output Out(sym).
Label: TypeAlias = In[InputType] | Out[OutputType]
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
        returns QUIESCENCE and stays in the current state if no output is enabled.
        """
        if letter is not None:
            targets = self.current_state.successor_states(letter)
            if not targets:
                raise ValueError(f"input {letter} is not enabled in {self.current_state.state_id}")
            self.current_state = choice(targets)
            return None

        output = choice(list(self._enabled_outputs(self.current_state)))

        self.current_state = choice(self._successors(self.current_state, output))

        return output

    def _enabled_outputs(self, state: LtsState[InputType, OutputType]) -> set[Out[OutputType] | Out[Quiescence]]:
        """
        Returns the outputs enabled in a state. Quiescence is implicit: a state without outputs enables only QUIESCENCE.
        """
        outputs: set[Out[OutputType] | Out[Quiescence]] = set(state.outputs())
        if not outputs:
            return {QUIESCENCE}
        else:
            return outputs

    def _successors(self, state: LtsState[InputType, OutputType], label: Label) -> list[LtsState[InputType, OutputType]]:
        """
        Returns the successors of a state for a label. QUIESCENCE is an implicit self-loop on quiescent states and leads
        nowhere from states with outputs.
        """
        if label == QUIESCENCE:
            return [state] if not state.outputs() else []
        return state.successor_states(label)

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
        input_alphabet = set(self.get_input_alphabet())
        return all(s.inputs() == input_alphabet for s in self.states)

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
        """
        outputs = set()

        for state in states:
            outputs |= self._enabled_outputs(state)

        return outputs

    def after_states(self, states: set[LtsState], trace: Trace) -> set[LtsState]:
        resulting_states: set[LtsState] = set()
        for state in states:
            resulting_states = resulting_states | (self.after(state, trace))

        return resulting_states

    def after(self, state: LtsState[InputType, OutputType], trace: Trace) -> set[LtsState[InputType, OutputType]]:
        """
        Given a state in the LTS and a trace, we return the set of states were 
        we can end up from the given state after sigma
        """
        states = set()
        if trace == []:
            states.add(state)
        else:
            current_label = trace[0]
            new_trace = trace[1:]
            for successor in self._successors(state, current_label):
                states = states | self.after(successor, new_trace)

        return states

    def to_state_setup(self) -> dict:
        """
        Converts the LTS to a state setup dictionary. The initial state is the first entry.

        :return dict: Map from state_id to a dict mapping (label_type_value, symbol) to a list of target state_ids,
            e.g. {'s0': {('?', 'coin'): ['s1']}, 's1': {('!', 'coffee'): ['s0']}}.
        """
        state_setup_dict = {}

        # ensure initial state is first in the dict
        ordered_states = [self.initial_state] + [s for s in self.states if s != self.initial_state]

        for s in ordered_states:
            state_setup_dict[s.state_id] = {('?' if isinstance(label, In) else '!',
                                             QUIESCENCE_SYMBOL if label == QUIESCENCE else label.sym):
                                                [target.state_id for target in targets]
                                            for label, targets in s.transitions.items()}

        return state_setup_dict

    @staticmethod
    def _states_from_setup(state_setup: dict) -> tuple[LtsState, list[LtsState]]:
        """
        Builds the states of a state setup dictionary, returning the initial state and all states.
        The output symbol QUIESCENCE_SYMBOL is mapped to QUIESCENCE.
        """
        states_map = {key: LtsState(key) for key in state_setup.keys()}

        for key, transitions in state_setup.items():
            source = states_map[key]
            for (kind, sym), targets in transitions.items():
                for target in targets:
                    if kind == '?':
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
            target state_ids, where label_type_value is '?' for inputs and '!' for outputs.
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
        Checks that every state enables at least one output (QUIESCENCE counts) and that the automaton is deterministic.
        Raises a ValueError otherwise.
        """
        for state in self.states:
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
