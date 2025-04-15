from abc import ABC, abstractmethod

class IObjectDetectionService(ABC):
    @abstractmethod
    def detect_objects(self, image_path):
        pass