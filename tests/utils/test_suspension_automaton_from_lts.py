import unittest

from aalpy.automata.Lts import Lts, SuspensionAutomaton, In, Out, QUIESCENCE
from aalpy.oracles import PerfectKnowledgeLtsOracle
from aalpy.SULs import LtsAutomatonSUL
from aalpy.utils import suspension_automaton_from_lts


def coffee_machine():
    """After a coin, the machine non-deterministically serves coffee (back to s0) or tea (to quiescent s2)."""
    return Lts.from_state_setup({
        's0': {('?', 'coin'): ['s1']},
        's1': {('!', 'coffee'): ['s0'], ('!', 'tea'): ['s2']},
        's2': {('?', 'coin'): ['s1']},
    })


def nondeterministic_input():
    """After ?a the system is either in s1, which outputs !x, or in the quiescent s2."""
    return Lts.from_state_setup({
        's0': {('?', 'a'): ['s1', 's2']},
        's1': {('!', 'x'): ['s0'], ('?', 'a'): ['s1']},
        's2': {('?', 'a'): ['s2']},
    })


def internal_choice():
    """s0 internally moves to s1, which outputs !x, or to the quiescent s2."""
    return Lts.from_state_setup({
        's0': {('τ', None): ['s1', 's2']},
        's1': {('!', 'x'): ['s0'], ('?', 'a'): ['s1']},
        's2': {('?', 'a'): ['s2']},
    })


def suspension_traces_equal(lts, sa):
    oracle = PerfectKnowledgeLtsOracle(lts.get_input_alphabet(), LtsAutomatonSUL(lts), lts)
    return oracle.find_cex(sa) is None


class SuspensionAutomatonFromLtsTests(unittest.TestCase):

    def test_deterministic_lts(self):
        sa = suspension_automaton_from_lts(coffee_machine())
        self.assertIsInstance(sa, SuspensionAutomaton)
        self.assertEqual(sa.to_state_setup(), {
            's0': {('!', 'δ'): ['s0'], ('?', 'coin'): ['s1']},
            's1': {('!', 'coffee'): ['s0'], ('!', 'tea'): ['s2']},
            's2': {('!', 'δ'): ['s2'], ('?', 'coin'): ['s1']},
        })

    def test_quiescent_states_get_delta_self_loop(self):
        sa = suspension_automaton_from_lts(coffee_machine())
        s0 = sa.initial_state
        self.assertEqual(s0.successor_states(QUIESCENCE), [s0])

    def test_nondeterminism_is_determinized(self):
        sa = suspension_automaton_from_lts(nondeterministic_input())
        after_a = sa.initial_state.successor_states(In('a'))[0]
        self.assertEqual(sa.out({after_a}), {Out('x'), QUIESCENCE})

        # δ from {s1, s2} only keeps the quiescent s2, after which !x is no longer possible
        after_a_delta = after_a.successor_states(QUIESCENCE)[0]
        self.assertEqual(sa.out({after_a_delta}), {QUIESCENCE})
        self.assertEqual(after_a_delta.successor_states(QUIESCENCE), [after_a_delta])

    def test_tau_transitions_are_removed(self):
        sa = suspension_automaton_from_lts(internal_choice())
        initial = sa.initial_state
        # the initial state is q0 after ε = {s0, s1, s2}, where s0 is not quiescent since it has a τ transition
        self.assertEqual(sa.out({initial}), {Out('x'), QUIESCENCE})
        self.assertEqual(initial.successor_states(Out('x')), [initial])

        after_delta = initial.successor_states(QUIESCENCE)[0]
        self.assertEqual(sa.out({after_delta}), {QUIESCENCE})

        after_a = initial.successor_states(In('a'))[0]
        self.assertEqual(sa.out({after_a}), {Out('x'), QUIESCENCE})

    def test_validate_rejects_tau(self):
        sa = SuspensionAutomaton.from_state_setup({'q0': {('!', 'δ'): ['q0'], ('τ', None): ['q0']}})
        with self.assertRaises(ValueError):
            sa.validate()

    def test_result_is_valid(self):
        for lts in (coffee_machine(), nondeterministic_input(), internal_choice()):
            suspension_automaton_from_lts(lts).validate()

    def test_traces_are_suspension_traces(self):
        # Lemma 6.3 of Janssen & Tretmans 2019: traces(Γ(s)) = Straces(s)
        for lts in (coffee_machine(), nondeterministic_input(), internal_choice()):
            self.assertTrue(suspension_traces_equal(lts, suspension_automaton_from_lts(lts)))


if __name__ == '__main__':
    unittest.main()
