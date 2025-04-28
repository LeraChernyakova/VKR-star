from abc import ABC, abstractmethod


class IAstrometryService(ABC):
    @abstractmethod
    def calibrate_image(self, image_path, timeout):
        pass
