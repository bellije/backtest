import abc
from dataclasses import dataclass
from enum import Enum

class StrategyOutputType(Enum):
    REBALANCE = "rebalance"
    SIGNAL = "signal"
    NONE = None

@dataclass
class TradeInstruction:
    type: int             # For trading signal, 1: Long, 0: Out, -1: Short
    weight: float = 0.0     # To get the proportion of capital allocated

@dataclass
class StrategyOutput:
    type: StrategyOutputType              # Can be rebalance or trading signal
    data: dict[str: TradeInstruction]

class Strategy(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'initiate_strategy') and 
                callable(subclass.initiate_strategy) and 
                hasattr(subclass, 'generate_signal') and 
                callable(subclass.generate_signal))

    @abc.abstractmethod
    def initiate_strategy(self, data):
        raise NotImplementedError 

    @abc.abstractmethod
    def generate_signal(self, date, prices) -> StrategyOutput:
        raise NotImplementedError