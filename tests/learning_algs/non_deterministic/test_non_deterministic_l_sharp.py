import unittest
from time import perf_counter

from aalpy.automata.Lts import Lts, SuspensionAutomaton, Trace
from aalpy.learning_algs.non_deterministic.NonDeterministicLSharp import NonDeterministicLSharp
from aalpy.SULs.LtsAutomatonSUL import LtsAutomatonSUL
from aalpy.oracles.PerfectKnowledgeLtsOracle import PerfectKnowledgeLtsOracle


def coffee_machine():
    """After a coin, the machine non-deterministically serves coffee (back to s0) or tea (to quiescent s2)."""
    return Lts.from_state_setup({
        's0': {('?', 'coin'): ['s1']},
        's1': {('?', 'coin'): ['s1'], ('!', 'coffee'): ['s0'], ('!', 'tea'): ['s2']},
        's2': {('?', 'coin'): ['s1']},
    })

def mqtt_broker():
    return Lts.from_state_setup({
        's0': {('?', 'connect'): ['s0_connect'],
                ('?', 'disconnect'): ['s0_disconnect'],
                ('?', 'subscribe'): ['s0_subscribe'],
                ('?', 'unsubscribe'): ['s0_unsubscribe'],
                ('?', 'publish'): ['s0_publish'],
        },
        's1': {('?', 'connect'): ['s1_connect'],
                ('?', 'disconnect'): ['s1_disconnect'],
                ('?', 'subscribe'): ['s1_subscribe'],
                ('?', 'unsubscribe'): ['s1_unsubscribe'],
                ('?', 'publish'): ['s1_publish'],
        },
        's2': {('?', 'connect'): ['s2_connect'],
                ('?', 'disconnect'): ['s2_disconnect'],
                ('?', 'subscribe'): ['s2_subscribe'],
                ('?', 'unsubscribe'): ['s2_unsubscribe'],
                ('?', 'publish'): ['s2_publish'],
        },
        's0_connect': {
            ('?', 'connect'): ['s0_connect'],
            ('?', 'disconnect'): ['s0_connect'],
            ('?', 'subscribe'): ['s0_connect'],
            ('?', 'unsubscribe'): ['s0_connect'],
            ('?', 'publish'): ['s0_connect'],
            ('!', 'CONNACK'): ['s1']
        },
        's0_disconnect': {('?', 'connect'): ['s0_disconnect'],
                        ('?', 'disconnect'): ['s0_disconnect'],
                        ('?', 'subscribe'): ['s0_disconnect'],
                        ('?', 'unsubscribe'): ['s0_disconnect'],
                        ('?', 'publish'): ['s0_disconnect'],
                        ('!', 'CONCLOSED_ALL'): ['s0']},
        's0_subscribe': {('?', 'connect'): ['s0_subscribe'],
                        ('?', 'disconnect'): ['s0_subscribe'],
                        ('?', 'subscribe'): ['s0_subscribe'],
                        ('?', 'unsubscribe'): ['s0_subscribe'],
                        ('?', 'publish'): ['s0_subscribe'],
                        ('!', 'CONCLOSED_ALL'): ['s0']},
        's0_unsubscribe': {('?', 'connect'): ['s0_unsubscribe'],
                            ('?', 'disconnect'): ['s0_unsubscribe'],
                            ('?', 'subscribe'): ['s0_unsubscribe'],
                            ('?', 'unsubscribe'): ['s0_unsubscribe'],
                            ('?', 'publish'): ['s0_unsubscribe'],
                            ('!', 'CONCLOSED_ALL'): ['s0']},
        's0_publish': {('?', 'connect'): ['s0_publish'],
                        ('?', 'disconnect'): ['s0_publish'],
                        ('?', 'subscribe'): ['s0_publish'],
                        ('?', 'unsubscribe'): ['s0_publish'],
                        ('?', 'publish'): ['s0_publish'],
                        ('!', 'CONCLOSED_ALL'): ['s0']},
        's1_connect': {('?', 'connect'): ['s1_connect'],
                        ('?', 'disconnect'): ['s1_connect'],
                        ('?', 'subscribe'): ['s1_connect'],
                        ('?', 'unsubscribe'): ['s1_connect'],
                        ('?', 'publish'): ['s1_connect'],
                        ('!', 'CONCLOSED_ALL'): ['s0'],
                        ('!', 'CONNACK'): ['s1'],
                        ('!', 'CONCLOSED_UNSUB_ALL'): ['s1']},
        's1_disconnect': {('?', 'connect'): ['s1_disconnect'],
                        ('?', 'disconnect'): ['s1_disconnect'],
                        ('?', 'subscribe'): ['s1_disconnect'],
                        ('?', 'unsubscribe'): ['s1_disconnect'],
                        ('?', 'publish'): ['s1_disconnect'],
                        ('!', 'CONCLOSED_ALL'): ['s0'],
                        ('!', 'CONCLOSED'): ['s1'],
                        ('!', 'CONCLOSED_UNSUB_ALL'): ['s1']},
        's1_subscribe': {('?', 'connect'): ['s1_subscribe'],
                        ('?', 'disconnect'): ['s1_subscribe'],
                        ('?', 'subscribe'): ['s1_subscribe'],
                        ('?', 'unsubscribe'): ['s1_subscribe'],
                        ('?', 'publish'): ['s1_subscribe'],
                        ('!', 'SUBACK'): ['s2'],
                        ('!', 'CONCLOSED'): ['s1']},
        's1_unsubscribe': {('?', 'connect'): ['s1_unsubscribe'],
                            ('?', 'disconnect'): ['s1_unsubscribe'],
                            ('?', 'subscribe'): ['s1_unsubscribe'],
                            ('?', 'unsubscribe'): ['s1_unsubscribe'],
                            ('?', 'publish'): ['s1_unsubscribe'],
                            ('!', 'UNSUBACK_ALL'): ['s1'],
                            ('!', 'CONCLOSED'): ['s1']},
        's1_publish': {('?', 'connect'): ['s1_publish'],
                        ('?', 'disconnect'): ['s1_publish'],
                        ('?', 'subscribe'): ['s1_publish'],
                        ('?', 'unsubscribe'): ['s1_publish'],
                        ('?', 'publish'): ['s1_publish'],
                        ('!', 'PUBACK'): ['s1'],
                        ('!', 'CONCLOSED'): ['s1']},
        's2_connect': {('?', 'connect'): ['s2_connect'],
                        ('?', 'disconnect'): ['s2_connect'],
                        ('?', 'subscribe'): ['s2_connect'],
                        ('?', 'unsubscribe'): ['s2_connect'],
                        ('?', 'publish'): ['s2_connect'],
                        ('!', 'CONCLOSED_ALL'): ['s0'],
                        ('!', 'CONNACK'): ['s2'],
                        ('!', 'CONCLOSED'): ['s2'],
                        ('!', 'CONCLOSED_UNSUB_ALL'): ['s1']},
        's2_disconnect': {('?', 'connect'): ['s2_disconnect'],
                        ('?', 'disconnect'): ['s2_disconnect'],
                        ('?', 'subscribe'): ['s2_disconnect'],
                        ('?', 'unsubscribe'): ['s2_disconnect'],
                        ('?', 'publish'): ['s2_disconnect'],
                        ('!', 'CONCLOSED_ALL'): ['s0'],
                        ('!', 'CONCLOSED'): ['s2'],
                        ('!', 'CONCLOSED_UNSUB_ALL'): ['s1']},
        's2_subscribe': {('?', 'connect'): ['s2_subscribe'],
                        ('?', 'disconnect'): ['s2_subscribe'],
                        ('?', 'subscribe'): ['s2_subscribe'],
                        ('?', 'unsubscribe'): ['s2_subscribe'],
                        ('?', 'publish'): ['s2_subscribe'],
                        ('!', 'SUBACK'): ['s2'],
                        ('!', 'CONCLOSED'): ['s2']},
        's2_unsubscribe': {('?', 'connect'): ['s2_unsubscribe'],
                            ('?', 'disconnect'): ['s2_unsubscribe'],
                            ('?', 'subscribe'): ['s2_unsubscribe'],
                            ('?', 'unsubscribe'): ['s2_unsubscribe'],
                            ('?', 'publish'): ['s2_unsubscribe'],
                            ('!', 'UNSUBACK_ALL'): ['s1'],
                            ('!', 'CONCLOSED'): ['s2'],
                            ('!', 'UNSUBACK'): ['s2']},
        's2_publish': {('?', 'connect'): ['s2_publish'],
                        ('?', 'disconnect'): ['s2_publish'],
                        ('?', 'subscribe'): ['s2_publish'],
                        ('?', 'unsubscribe'): ['s2_publish'],
                        ('?', 'publish'): ['s2_publish'],
                        ('!', 'CONCLOSED'): ['s2'],
                        ('!', 'PUBACK_PUBLISH'): ['s2']}
                
})

def volpato_tretmans_2_iots():
    """The example IOTS used in the paper 'Approximate Active Learning of Nondeterministic Input Output Transition Systems' by Michele Volpato and Jan Tretmans"""
    return Lts.from_state_setup({
        's0': {('?', 'a'): ['s1']},
        's1': {('?', 'a'): ['s2']},
        's2': {('?', 'a'): ['s2'], ('!', 'y'): ['s2'], ('!', 'x'): ['s0']}
    })

def volpato_tretmans_1_iots():
    """The example IOTS used in the paper 'Active Learning of Nondeterministic Systems from an ioco Perspective' by Michele Volpato and Jan Tretmans"""
    return Lts.from_state_setup({
        's0': {('?', 'a'): ['s1', 's2']},
        's1': {('?', 'a'): ['s1'], ('!', 'x'): ['s3']},
        's2': {('?', 'a'): ['s4']},
        's3': {('?', 'a'): ['s3'], ('!', 'x'): ['s5']},
        's4': {('?', 'a'): ['s4'], ('!', 'x'): ['s6']},
        's5': {('?', 'a'): ['s5']},
        's6': {('?', 'a'): ['s6'], ('!', 'y'): ['s5']},
    })


class TestRunNonDeterministicLSharp(unittest.TestCase):
    def learn_sul(self, iots : Lts, show_learned_model: bool = False, show_original_model: bool = False) -> SuspensionAutomaton:
        sul = LtsAutomatonSUL(iots)
        
        if show_original_model:
            iots.visualize()

        learn_algorithm = NonDeterministicLSharp(set(iots.get_input_alphabet()), sul, iots)

        hypothesis = learn_algorithm.run()

        if show_learned_model:
            hypothesis.visualize()
        
        return hypothesis

    def check_counter_example(self, iots: Lts, hypothesis: SuspensionAutomaton) -> (Trace | None):
        sul = LtsAutomatonSUL(iots)
        eq_oracle = PerfectKnowledgeLtsOracle(iots.get_input_alphabet(), sul, iots)
        return eq_oracle.find_cex(hypothesis)

    def test_learn_coffee_machine(self):
        coffee_machine_lts = coffee_machine()

        learned_sul = self.learn_sul(coffee_machine_lts)
        cex = self.check_counter_example(coffee_machine_lts, learned_sul)

        self.assertIsNone(cex)

    def test_statistics(self):
        coffee_machine_lts = coffee_machine()
        sul = LtsAutomatonSUL(coffee_machine_lts)

        learn_algorithm = NonDeterministicLSharp(set(coffee_machine_lts.get_input_alphabet()), sul, coffee_machine_lts)

        learn_algorithm.run()

        stats = learn_algorithm.observation_tree.get_current_stats()

        expected = {
            'promotion_rule_calls': 1,
            'extension_rule_calls': 2,
            'completion_rule_calls': 2,
            'identification_rule_calls': 2,
            'stable_rule_calls': 0,
            'conflict_processing_rule_calls': 0,
            'quiescent_reducible_rule_calls': 0,
            'equivalence_rule_calls': 1,
            'equivalence_query_calls': 1,
            'nr_of_tree_states': 9,
            'nr_of_hypothesis_states': 2,
        }

        actual = {key: stats.get(key) for key in expected}
        self.assertEqual(actual, expected)

    def test_learn_mqtt(self):
        mqtt_lts = mqtt_broker()

        learned_sul = self.learn_sul(mqtt_lts)
        cex = self.check_counter_example(mqtt_lts, learned_sul)

        self.assertIsNone(cex)

    def test_learn_volpato_tretmans_2_iots(self):
        iots = volpato_tretmans_2_iots()

        learned_sul = self.learn_sul(iots)
        cex = self.check_counter_example(iots, learned_sul)

        self.assertIsNone(cex)

    def test_learn_volpato_tretmans_1_iots(self):
        iots = volpato_tretmans_1_iots()

        learned_sul = self.learn_sul(iots)
        cex = self.check_counter_example(iots, learned_sul)

        self.assertIsNone(cex)

class TestRunQueryBenchMarks(unittest.TestCase):
    def print_statistics(self, statistics: dict[str, int|float]):
        labels = {name: name.replace('_', ' ').capitalize() for name in statistics}
        width = max(map(len, labels.values()), default=0)

        line = '-' * (width + 12)
        print(f'\n{line}')
        for name, value in statistics.items():
            print(f'{labels[name]:<{width}}  {value:>8}')
        print(line)

    def run_benchmark(self, iots : Lts, show_learned_model: bool = False, show_original_model: bool = False, show_tree: bool = False, show_stats: bool = True) -> SuspensionAutomaton:
        sul = LtsAutomatonSUL(iots)
                
        if show_original_model:
            iots.visualize()


        learn_algorithm = NonDeterministicLSharp(set(iots.get_input_alphabet()), sul, iots)

        start = perf_counter()
        hypothesis = learn_algorithm.run()
        end = perf_counter()

        if show_tree:
            learn_algorithm.observation_tree.save_dot('tree.dot')

        if show_learned_model:
            hypothesis.visualize()

        if show_stats:
            stats = learn_algorithm.get_statistics()

            stats['runtime_(seconds)'] = round(end - start, 4)

            self.print_statistics(stats)



        
        return hypothesis

    def test_benchmark_coffee_machine(self):
        coffee_machine_lts = coffee_machine()

        self.run_benchmark(coffee_machine_lts)

    def test_benchmark_volpato_tretmans_1_iots(self):
        iots = volpato_tretmans_1_iots()
        self.run_benchmark(iots)

    def test_benchmark_volpato_tretmans_2_iots(self):
        iots = volpato_tretmans_2_iots()
        self.run_benchmark(iots)

    def test_benchmark_mqtt(self):
        mqtt_lts = mqtt_broker()
        self.run_benchmark(mqtt_lts)



