import unittest

from aalpy.automata.Lts import Lts
from aalpy.learning_algs.non_deterministic.NonDeterministicLSharp import run_non_deterministic_l_sharp
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



class TestRunNonDeterministicLSharp(unittest.TestCase):
    def test_learn_coffee_machine(self):
        coffee_machine_lts = coffee_machine()
        sul = LtsAutomatonSUL(coffee_machine_lts)

        learned_sul = run_non_deterministic_l_sharp(set(coffee_machine_lts.get_input_alphabet()), sul, coffee_machine_lts)

        eq_oracle = PerfectKnowledgeLtsOracle(coffee_machine_lts.get_input_alphabet(), sul, coffee_machine_lts)

        cex = eq_oracle.find_cex(learned_sul)

        self.assertIsNone(cex)

    def test_learn_mqtt(self):
        mqtt_lts = mqtt_broker()
        sul = LtsAutomatonSUL(mqtt_lts)

        learned_sul = run_non_deterministic_l_sharp(set(mqtt_lts.get_input_alphabet()), sul, mqtt_lts)

        eq_oracle = PerfectKnowledgeLtsOracle(mqtt_lts.get_input_alphabet(), sul, mqtt_lts)

        cex = eq_oracle.find_cex(learned_sul)

        self.assertIsNone(cex)