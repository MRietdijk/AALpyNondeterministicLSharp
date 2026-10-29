import unittest

from aalpy.automata.Lts import Lts, SuspensionAutomaton, In, Out, QUIESCENCE
from aalpy.oracles import PerfectKnowledgeLtsOracle
from aalpy.SULs import LtsAutomatonSUL


def coffee_machine():
    """After a coin, the machine non-deterministically serves coffee (back to s0) or tea (to quiescent s2)."""
    return Lts.from_state_setup({
        's0': {('?', 'coin'): ['s1']},
        's1': {('!', 'coffee'): ['s0'], ('!', 'tea'): ['s2']},
        's2': {('?', 'coin'): ['s1']},
    })


def coffee_machine_sa():
    """Suspension automaton of coffee_machine, with explicit δ self-loops on the quiescent states."""
    return SuspensionAutomaton.from_state_setup({
        'q0': {('?', 'coin'): ['q1'], ('!', 'δ'): ['q0']},
        'q1': {('!', 'coffee'): ['q0'], ('!', 'tea'): ['q2']},
        'q2': {('?', 'coin'): ['q1'], ('!', 'δ'): ['q2']},
    })


def coffee_machine_sa_without_tea():
    return SuspensionAutomaton.from_state_setup({
        'q0': {('?', 'coin'): ['q1'], ('!', 'δ'): ['q0']},
        'q1': {('!', 'coffee'): ['q0']},
    })


def coffee_machine_sa_wrong_quiescence():
    """δ from q2 leads to q1 instead of looping, so after δ the hypothesis enables coffee and tea."""
    return SuspensionAutomaton.from_state_setup({
        'q0': {('?', 'coin'): ['q1'], ('!', 'δ'): ['q0']},
        'q1': {('!', 'coffee'): ['q0'], ('!', 'tea'): ['q2']},
        'q2': {('?', 'coin'): ['q1'], ('!', 'δ'): ['q1']},
    })


def make_oracle():
    model = coffee_machine()
    return PerfectKnowledgeLtsOracle(model.get_input_alphabet(), LtsAutomatonSUL(model), model)


class LtsQuiescenceTests(unittest.TestCase):

    def test_implicit_quiescence_in_lts(self):
        model = coffee_machine()
        s0, s1 = model.states[0], model.states[1]
        self.assertEqual(model.out({s0}), {QUIESCENCE})
        self.assertEqual(model.after(s0, [QUIESCENCE]), {s0})
        self.assertEqual(model.after(s1, [QUIESCENCE]), set())

    def test_explicit_quiescence_in_suspension_automaton(self):
        sa = coffee_machine_sa_wrong_quiescence()
        q1, q2 = sa.states[1], sa.states[2]
        self.assertEqual(sa.after(q2, [QUIESCENCE]), {q1})
        self.assertIn(QUIESCENCE, sa.out({q2}))
        self.assertNotIn(QUIESCENCE, sa.out({q1}))

    def test_state_setup_round_trip_keeps_quiescence(self):
        sa = coffee_machine_sa()
        self.assertEqual(SuspensionAutomaton.from_state_setup(sa.to_state_setup()).to_state_setup(), sa.to_state_setup())
        self.assertIn(QUIESCENCE, sa.initial_state.transitions)

    def test_validate(self):
        coffee_machine_sa().validate()
        with self.assertRaises(ValueError):
            SuspensionAutomaton.from_state_setup({'q0': {('?', 'coin'): ['q0']}}).validate()
        with self.assertRaises(ValueError):
            SuspensionAutomaton.from_state_setup({'q0': {('!', 'a'): ['q0', 'q1']}, 'q1': {('!', 'δ'): ['q1']}}).validate()


class PerfectKnowledgeCompletenessOracleTests(unittest.TestCase):

    def test_complete_output_set(self):
        oracle = make_oracle()
        self.assertIsNone(oracle.completeness_query([In('coin')], {Out('coffee'), Out('tea')}))
        self.assertIsNone(oracle.completeness_query([], {QUIESCENCE}))

    def test_incomplete_output_set(self):
        oracle = make_oracle()
        self.assertEqual(oracle.completeness_query([In('coin')], {Out('coffee')}), Out('tea'))
        self.assertEqual(oracle.completeness_query([], set()), QUIESCENCE)

    def test_invalid_queries_raise(self):
        oracle = make_oracle()
        with self.assertRaises(ValueError):
            oracle.completeness_query([In('coin'), In('coin')], set())
        with self.assertRaises(ValueError):
            oracle.completeness_query([In('coin')], {Out('coffee'), Out('milk')})

    def test_equivalent_hypothesis(self):
        self.assertIsNone(make_oracle().find_cex(coffee_machine_sa()))

    def test_missing_output(self):
        self.assertEqual(make_oracle().find_cex(coffee_machine_sa_without_tea()), [In('coin'), Out('tea')])

    def test_wrong_quiescence_target(self):
        self.assertEqual(make_oracle().find_cex(coffee_machine_sa_wrong_quiescence()),
                         [In('coin'), Out('tea'), QUIESCENCE, Out('coffee')])


if __name__ == '__main__':
    unittest.main()
