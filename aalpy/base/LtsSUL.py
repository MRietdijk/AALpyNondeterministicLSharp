from abc import ABC, abstractmethod
from aalpy.automata.Lts import In, Out, Trace

class LtsSUL(ABC):


    def __init__(self) -> None:
        """
        Creates an Labelled Transition System SUL with zeroed steps/queries
        """

        self.num_steps = 0
        self.num_queries = 0

    @abstractmethod
    def step_input(self, input_label: In) -> None:
        pass

    @abstractmethod
    def observe_output(self) -> Out:
        pass

    @abstractmethod
    def pre(self) -> None:
        pass

    @abstractmethod
    def post(self) -> None:
        pass

    def query(self, trace: Trace) -> Trace:
        """
        Performs the trace on the SUL. If the trace could not be executed (because there was an output in the trace which was not observed), the function returns early with the observed output.

        """
        self.pre()
        self.num_queries += 1
        observed = []

        for label in trace:
            self.num_steps += 1
            if isinstance(label, In):
                self.step_input(label)
                observed.append(label)
            else:
                out = self.observe_output()
                observed.append(out)
                if out != label:
                    self.post()
                    return observed

        self.num_steps += 1
        observed.append(self.observe_output())
        self.post()

        return observed
        
