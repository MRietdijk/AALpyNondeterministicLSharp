from aalpy.automata.Lts import In, Out
from aalpy.base import LtsSUL
from aalpy.automata import Lts

class LtsAutomatonSUL(LtsSUL):
    """
    System under learning that wraps an in-memory automaton, delegating steps to it.
    """

    def __init__(self, lts: Lts) -> None:
        super().__init__()
        self.lts = lts

    def pre(self) -> None:
        self.lts.reset_to_initial()

    def post(self) -> None:
        pass

    def step_input(self, input_label: In) -> None:
        return self.lts.step(input_label)

    def observe_output(self) -> Out:
        return self.lts.step(None)

    