from abc import ABC, abstractmethod


class IFileSelectionService(ABC):
    @abstractmethod
    def select_image(self):
        pass