from abc import ABC, abstractmethod
from aalpy.automata.Lts import In, Lts, Trace, Out
from aalpy.base import LtsSUL


class LtsOracle(ABC):

    def __init__(self, input_alphabet: list[In], sul: LtsSUL) -> None:
        self.input_alphabet = input_alphabet
        self.sul = sul
        self.num_queries = 0
        self.num_steps = 0

    @abstractmethod
    def find_cex(self, hypothesis: Lts) -> Trace | None:
        pass

    @abstractmethod
    def completeness_query(self, trace: Trace, outputs: set[Out]) -> Out | None:
        pass