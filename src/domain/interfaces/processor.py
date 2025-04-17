from abc import ABC, abstractmethod

class IProcessor(ABC):
    @abstractmethod
    def process(self, data):
        pass