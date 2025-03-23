from abc import ABC, abstractmethod

class ProcessingChain(ABC):
    def __init__(self, next_processor=None):
        self.next_processor = next_processor

    def process(self, data):
        result = self.handle(data)
        if result and self.next_processor:
            return self.next_processor.process(result)
        return result

    @abstractmethod
    def handle(self, data):
        pass