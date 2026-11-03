import unittest

from aalpy.automata.Lts import Lts, In, Out, QUIESCENCE, TAU


def tau_lts():
    """s0 internally moves to s1 (which outputs !x) or to the quiescent s2."""
    return Lts.from_state_setup({
        's0': {('τ', None): ['s1', 's2']},
        's1': {('!', 'x'): ['s0'], ('?', 'a'): ['s1']},
        's2': {('?', 'a'): ['s2']},
    })


class LtsTauTests(unittest.TestCase):

    def setUp(self):
        self.lts = tau_lts()
        self.s0, self.s1, self.s2 = self.lts.states

    def test_tau_closure(self):
        self.assertEqual(self.lts.tau_closure({self.s0}), {self.s0, self.s1, self.s2})
        self.assertEqual(self.lts.tau_closure({self.s1}), {self.s1})

    def test_state_with_only_tau_is_not_quiescent(self):
        self.assertFalse(self.s0.is_quiescent())
        self.assertTrue(self.s2.is_quiescent())
        self.assertEqual(self.lts.after(self.s0, [QUIESCENCE]), {self.s2})

    def test_after_empty_trace_is_tau_closed(self):
        self.assertEqual(self.lts.after(self.s0, []), {self.s0, self.s1, self.s2})

    def test_after_takes_tau_after_label(self):
        self.assertEqual(self.lts.after(self.s1, [Out('x')]), {self.s0, self.s1, self.s2})

    def test_out_sees_through_tau(self):
        self.assertEqual(self.lts.out({self.s0}), {Out('x'), QUIESCENCE})

    def test_inputs_are_weakly_enabled(self):
        self.assertEqual(self.lts.after(self.s0, [In('a')]), {self.s1, self.s2})
        self.assertTrue(self.lts.is_input_complete())

    def test_step_never_returns_tau(self):
        for _ in range(50):
            self.lts.reset_to_initial()
            self.assertIn(self.lts.step(None), {Out('x'), QUIESCENCE})
            self.assertIsNone(self.lts.step(In('a')))
            self.assertIn(self.lts.step(None), {Out('x'), QUIESCENCE})

    def test_state_setup_round_trip(self):
        setup = self.lts.to_state_setup()
        self.assertEqual(setup['s0'], {('τ', None): ['s1', 's2']})
        self.assertEqual(Lts.from_state_setup(setup).to_state_setup(), setup)
        self.assertIn(TAU, Lts.from_state_setup(setup).initial_state.transitions)


if __name__ == '__main__':
    unittest.main()
