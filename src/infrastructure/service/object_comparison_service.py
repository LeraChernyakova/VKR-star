import numpy as np

from scipy.spatial import cKDTree

from src.domain.interfaces.object_comparison_service import IObjectComparisonService
from src.infrastructure.utils.logger import Logger


class ObjectComparisonService(IObjectComparisonService):
    def __init__(self):
        self.service_name = "ObjectComparisonService"
        self.logger = Logger()

    def find_unique_objects(self, detected_objects, reference_objects, match_threshold=10):
        if not detected_objects:
            return []

        if not reference_objects:
            return detected_objects

        unique_objects = []

        ref_coords = np.array([[coord[0], coord[1]] for coord in reference_objects])

        for obj in detected_objects:
            x, y = obj["x"], obj["y"]

            distances = np.sqrt((ref_coords[:, 0] - x) ** 2 + (ref_coords[:, 1] - y) ** 2)

            if np.min(distances) > match_threshold:
                unique_objects.append(obj)

        return unique_objects