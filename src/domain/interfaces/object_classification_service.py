from abc import ABC, abstractmethod

class IObjectClassificationService(ABC):
    @abstractmethod
    def classify_objects(self, objects_data):
        pass