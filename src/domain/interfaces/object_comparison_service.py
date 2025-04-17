from abc import ABC, abstractmethod

class IObjectComparisonService(ABC):
    @abstractmethod
    def find_unique_objects(self, detected_objects, reference_objects, match_threshold):
        pass