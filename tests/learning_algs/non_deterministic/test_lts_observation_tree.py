import unittest

from aalpy.automata.Lts import Lts, In, Out, QUIESCENCE, Trace
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL
from aalpy.learning_algs.non_deterministic.LtsObservationTree import LtsObservationTree, LtsNode
from aalpy.oracles.PerfectKnowledgeLtsOracle import PerfectKnowledgeLtsOracle

def coffee_machine():
    """After a coin, the machine non-deterministically serves coffee (back to s0) or tea (to quiescent s2)."""
    return Lts.from_state_setup({
        's0': {('?', 'coin'): ['s1']},
        's1': {('?', 'coin'): ['s1'], ('!', 'coffee'): ['s0'], ('!', 'tea'): ['s2']},
        's2': {('?', 'coin'): ['s1']},
    })

def coffee_or_tea_choice_machine():
    """After a coin the machine non-deterministically serves coffee (to new state s2) or tea (to new state s3) afterwards, the observed output is only observed after throwing in coins"""
    return Lts.from_state_setup({
        's0': {('?', 'coin'): ['s1']},
        's1': {('?', 'coin'): ['s1'], ('!', 'coffee'): ['s2'], ('!', 'tea'): ['s3']},
        's2': {('?', 'coin'): ['s4']},
        's3': {('?', 'coin'): ['s5']},
        's4': {('!', 'coffee'): ['s2'], ('?', 'coin'): ['s4']},
        's5': {('!', 'tea'): ['s3'], ('?', 'coin'): ['s5']},
    })

class LtsObservationTreeTest(unittest.TestCase):
    
    def setUp(self) -> None:
        self.model: Lts = coffee_machine()
        self.sul = LtsAutomatonSUL(self.model)
        self.oracle = PerfectKnowledgeLtsOracle(self.model.get_input_alphabet(), self.sul, self.model)
        self.ob_tree = LtsObservationTree(set(self.model.get_input_alphabet()), self.sul, self.oracle)
        self.root = self.ob_tree.root

    def test_getting_frontier(self):
        frontier = self.ob_tree.get_frontier()
        self.assertEqual(len(frontier), 0)

        self.ob_tree.insert_observation([In('coin')])

        frontier = self.ob_tree.get_frontier()

        self.assertEqual(len(frontier), 1)

    def test_same_state_after_extending(self):
        q = self.root.extend_and_get(In('coin'))
        r = self.root.extend_and_get(In('coin'))

        self.assertIs(q, r)

    def test_quiescence_on_stable_node_is_a_self_loop(self):
        stable_node = self.root.extend_and_get(QUIESCENCE)
        same_node = stable_node.extend_and_get(QUIESCENCE)

        self.assertTrue(stable_node.is_stable)
        self.assertIs(stable_node, same_node)

    def test_quiescence_on_unstable_node_is_extension(self):
        unstable_node = self.root
        quiescence_successor = unstable_node.extend_and_get(QUIESCENCE)

        self.assertFalse(unstable_node.is_stable)
        self.assertIsNot(unstable_node, quiescence_successor)

    def test_correct_input_output_split(self):
        input_set = self.model.get_input_alphabet()
        output_set = self.model.get_output_alphabet()
        for label in input_set + output_set:
            self.root.extend_and_get(label)

        self.assertCountEqual(input_set, list(self.root.inputs()))
        self.assertCountEqual(output_set, list(self.root.outputs()))

    def test_no_witness_between_two_nodes_which_are_not_yet_apart(self):
        new_observation = [In('coin'), Out('coffee')]
        self.ob_tree.insert_observation(new_observation)

        q = self.ob_tree.tree_after(new_observation[:1])
        r = self.ob_tree.tree_after(new_observation)

        assert q is not None
        assert r is not None
        self.assertIsNone(q.get_witness(r))
        self.assertFalse(q.is_apart_from(r))


        self.assertIsNone(r.get_witness(q))
        self.assertFalse(r.is_apart_from(q))

    def test_trivial_witness_between_two_nodes_can_be_found(self):
        coffee_observation = [In('coin'), Out('coffee')]
        tea_observation = [In('coin'), Out('tea')]
        witnesses = [[Out('coffee')], [Out('tea')]]

        self.ob_tree.insert_observation([QUIESCENCE])
        self.ob_tree.insert_observation(coffee_observation)
        self.ob_tree.insert_observation(tea_observation)

        q = self.root
        r = self.ob_tree.tree_after([In('coin')])

        assert q is not None
        assert r is not None

        q.mark_complete()

        self.assertIsNotNone(r.get_witness(q))
        self.assertIsNotNone(q.get_witness(r))
        self.assertTrue(r.is_apart_from(q))
        self.assertTrue(q.is_apart_from(r))

        self.assertIn(r.get_witness(q), witnesses)
        self.assertIn(q.get_witness(r), witnesses)

    def test_after_quiescence_state_is_complete_and_extended_with_stable_quiescence(self):
        self.ob_tree.insert_observation([QUIESCENCE])

        q = self.ob_tree.tree_after([QUIESCENCE])

        assert q is not None

        self.assertTrue(q.is_stable)
        self.assertTrue(q.is_complete)
        self.assertIs(q, self.ob_tree.tree_after([QUIESCENCE, QUIESCENCE]))

    def test_no_apartness_between_states_if_not_one_of_them_is_complete(self):
        coffee_observation = [In('coin'), Out('coffee')]
        tea_observation = [In('coin'), Out('coffee')]

        self.ob_tree.insert_observation([QUIESCENCE])
        self.ob_tree.insert_observation(coffee_observation)
        self.ob_tree.insert_observation(tea_observation)


        q = self.root
        r = self.ob_tree.tree_after([In('coin')])

        assert q is not None
        assert r is not None

        self.assertIsNone(q.get_witness(r))
        self.assertIsNone(r.get_witness(q))
        self.assertFalse(q.is_apart_from(r))
        self.assertFalse(r.is_apart_from(q))

    def test_state_is_not_apart_from_itself(self):
        coffee_observation = [In('coin'), Out('coffee')]
        tea_observation = [In('coin'), Out('coffee')]

        self.ob_tree.insert_observation(coffee_observation)
        self.ob_tree.insert_observation(tea_observation)


        r = self.ob_tree.tree_after([In('coin')])

        assert r is not None

        r.mark_complete()

        self.assertIsNone(r.get_witness(r))
        self.assertFalse(r.is_apart_from(r))

    def test_apartness_witness_is_further(self):
        # does not follow the actual SUL, but is a nice test for apartness
        many_coins_coffee_observation = [In('coin')] + [Out('coffee')] + [In('coin')] * 8 + [Out('coffee')]
        many_coins_tea_observation = [In('coin')] + [Out('tea')] + [In('coin')] * 8 + [Out('tea')]

        self.ob_tree.insert_observation(many_coins_coffee_observation)
        self.ob_tree.insert_observation(many_coins_tea_observation)

        q = self.ob_tree.tree_after(many_coins_coffee_observation[:2])
        r = self.ob_tree.tree_after(many_coins_tea_observation[:2])
        q_prime = self.ob_tree.tree_after(many_coins_coffee_observation[:-1])
        r_prime = self.ob_tree.tree_after(many_coins_tea_observation[:-1])



        assert q is not None
        assert r is not None
        assert q_prime is not None
        assert r_prime is not None

        q_prime.mark_complete()


        self.assertTrue(q.is_apart_from(r))
        self.assertTrue(r.is_apart_from(q))

        self.assertEqual(q.get_witness(r), many_coins_tea_observation[2:])
        self.assertEqual(r.get_witness(q), many_coins_tea_observation[2:])

        r_prime.mark_complete()

        witnesses = [many_coins_tea_observation[2:], many_coins_coffee_observation[2:]]

        self.assertIn(q.get_witness(r), witnesses)
        self.assertIn(r.get_witness(q), witnesses)

    def test_apartness_will_terminate_for_two_stable_states(self):
        self.ob_tree.insert_observation([QUIESCENCE])
        self.ob_tree.insert_observation([In('coin'), QUIESCENCE])

        q = self.ob_tree.tree_after([QUIESCENCE])
        r = self.ob_tree.tree_after([In('coin'), QUIESCENCE])

        assert q is not None
        assert r is not None

        self.assertFalse(q.is_apart_from(r))
        self.assertFalse(r.is_apart_from(q))

    def test_tree_after_not_observed(self):
        self.assertEqual(self.ob_tree.tree_after([QUIESCENCE]), None)

    def test_get_access_sequence_for_just_observed_state(self):
        observation = [In('coin')] * 8 + [Out('tea')]
        observation_2 = [In('coin')] * 7 + [Out('coffee')]
        self.ob_tree.insert_observation(observation)
        self.ob_tree.insert_observation(observation_2)

        q = self.ob_tree.tree_after(observation)
        r = self.ob_tree.tree_after(observation_2)
        p = LtsNode()

        assert q is not None
        assert r is not None
        
        access_q = self.ob_tree.get_access_sequence(q)
        access_r = self.ob_tree.get_access_sequence(r)

        self.assertEqual(observation, access_q)
        self.assertEqual(observation_2, access_r)
        self.assertRaises(ValueError, self.ob_tree.get_access_sequence, p)


    def test_get_access_sequence_for_root(self):
        self.assertEqual(self.ob_tree.get_access_sequence(self.root), [])

    def test_stable_get_access_sequence(self):
        quiescence_trace: Trace = [QUIESCENCE] * 8
        self.ob_tree.insert_observation(quiescence_trace)

        q = self.ob_tree.tree_after(quiescence_trace)

        assert q is not None

        access_q = self.ob_tree.get_access_sequence(q)

        self.assertEqual([QUIESCENCE], access_q)

    def test_no_successor(self):
        self.ob_tree.insert_observation([In('coin')])
        self.ob_tree.insert_observation([Out('coffee')])
        
        self.assertIsNone(self.root.get_successor(QUIESCENCE))
        self.assertIsNotNone(self.root.get_successor(In('coin')))
        self.assertIsNotNone(self.root.get_successor(Out('coffee')))


    def test_extension_enabled_and_not_enabled(self):
        self.ob_tree.insert_observation([QUIESCENCE])

        self.assertTrue(self.root.is_enabled(QUIESCENCE))
        self.assertFalse(self.root.is_enabled(In('coin')))

class LtsObservationTreeOracleUsesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model: Lts = coffee_machine()
        self.sul = LtsAutomatonSUL(self.model)
        self.oracle = PerfectKnowledgeLtsOracle(self.model.get_input_alphabet(), self.sul, self.model)
        self.ob_tree = LtsObservationTree(set(self.model.get_input_alphabet()), self.sul, self.oracle)
        self.root = self.ob_tree.root

    def test_check_complete_output(self):
        b = self.ob_tree.check_complete_output(self.root)
        b_prime = self.ob_tree.check_complete_output(self.root)
        
        self.assertFalse(b)
        self.assertTrue(b_prime)

        self.assertIsNotNone(self.ob_tree.tree_after([QUIESCENCE]))
        self.assertTrue(self.root.is_enabled)

    def test_check_complete_output_after_coin(self):
        self.ob_tree.insert_observation([In('coin'), Out('tea')])

        q = self.ob_tree.tree_after([In('coin')])

        assert q is not None

        b = self.ob_tree.check_complete_output(q)
        b_prime = self.ob_tree.check_complete_output(q)

        self.assertFalse(b)
        self.assertTrue(b_prime)
        self.assertCountEqual(q.outputs(), set([Out('tea'), Out('coffee')]))


    def test_assertion_all_observations_in_tree_are_from_sul(self):
        self.ob_tree.insert_observation([In('coin'), Out('cappuchino')])

        q = self.ob_tree.tree_after([In('coin')])

        assert q is not None

        self.assertRaises(ValueError, self.ob_tree.check_complete_output, q)

    def test_do_empty_trace(self):
        self.assertTrue(self.ob_tree.do(self.root, []))

    def test_do_new_trace_in_tree(self):
        trace = [In('coin'), Out('coffee')]
        b = self.ob_tree.do(self.root, trace)
        q = self.ob_tree.tree_after(trace)

        self.assertTrue(b)
        self.assertIsNotNone(q)


    def test_do_new_trace_not_in_tree(self):
        trace = [In('coin'), Out('tea'), Out('coffee')]

        b = self.ob_tree.do(self.root, trace)
        q = self.ob_tree.tree_after(trace[:1])
        r = self.ob_tree.tree_after(trace[:2])

        assert q is not None
        assert r is not None

        self.assertFalse(b)
        self.assertIn(Out('tea'), q.outputs())
        self.assertTrue(r.is_complete)

    def test_do_quiescent_trace(self):
        trace: Trace = [QUIESCENCE] * 8

        b = self.ob_tree.do(self.root, trace)

        q = self.ob_tree.tree_after(trace[:1])

        assert q is not None

        self.assertTrue(b)
        self.assertTrue(q.is_complete)

class LtsObsercationTreeRules(unittest.TestCase):
    def setUp(self) -> None:
        self.model: Lts = coffee_machine()
        self.sul = LtsAutomatonSUL(self.model)
        self.oracle = PerfectKnowledgeLtsOracle(self.model.get_input_alphabet(), self.sul, self.model)
        self.ob_tree = LtsObservationTree(set(self.model.get_input_alphabet()), self.sul, self.oracle)
        self.root = self.ob_tree.root

    def test_extension_rule(self):
        b = self.ob_tree.extension_rule()
        q = self.ob_tree.tree_after([In('coin')])

        assert q is not None

        self.assertTrue(b)

        b_prime = self.ob_tree.extension_rule()

        self.assertFalse(b_prime)


class LtsObservationTreeBuildHypothesis(unittest.TestCase):
    def setUp(self) -> None:
        self.model: Lts = coffee_machine()
        self.sul = LtsAutomatonSUL(self.model)
        self.oracle = PerfectKnowledgeLtsOracle(self.model.get_input_alphabet(), self.sul, self.model)
        self.ob_tree = LtsObservationTree(set(self.model.get_input_alphabet()), self.sul, self.oracle)
        self.root = self.ob_tree.root

    def test_assumption_all_states_are_input_enabled(self):
        self.assertRaises(AssertionError, self.ob_tree.build_hypothesis)

    # def 



if __name__ == '__main__':
    unittest.main()

