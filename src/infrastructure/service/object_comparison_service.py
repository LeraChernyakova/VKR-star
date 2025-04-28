import numpy as np
from src.domain.interfaces.object_comparison_service import IObjectComparisonService
from src.infrastructure.utils.logger import Logger


class ObjectComparisonService(IObjectComparisonService):
    def __init__(self):
        self.service_name = "ObjectComparisonService"
        self.logger = Logger()

    def find_unique_objects(self, detected_objects, reference_objects, match_threshold=10):
        unique_objects = []

        reference_coords = np.array(reference_objects) if reference_objects else np.array([])

        for obj in detected_objects:
            x, y = obj['x'], obj['y']

            if len(reference_coords) > 0:
                distances = np.sqrt((reference_coords[:, 0] - x) ** 2 + (reference_coords[:, 1] - y) ** 2)
                if np.min(distances) > match_threshold:
                    unique_objects.append(obj)
            else:
                unique_objects.append(obj)

        return unique_objects