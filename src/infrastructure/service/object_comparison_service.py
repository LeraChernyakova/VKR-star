import numpy as np
from src.domain.interfaces.object_comparison_service import IObjectComparisonService
from src.infrastructure.utils.logger import Logger


class ObjectComparisonService(IObjectComparisonService):
    def __init__(self):
        self.service_name = "ObjectComparisonService"
        self.logger = Logger()

    def find_unique_objects(self, detected_objects, reference_objects, match_threshold=10):
        detected_coords = np.array(detected_objects)
        reference_coords = np.array(reference_objects) if reference_objects else np.array([])

        unique_objects = []

        for x, y in detected_coords:
            if len(reference_coords) > 0:
                distances = np.sqrt((reference_coords[:, 0] - x) ** 2 + (reference_coords[:, 1] - y) ** 2)
                if np.min(distances) > match_threshold:
                    unique_objects.append((x, y))
            else:
                unique_objects.append((x, y))

        return unique_objects