import numpy as np

from scipy.spatial import KDTree
from src.infrastructure.utils.logger import Logger
from src.domain.interfaces.object_comparison_service import IObjectComparisonService


class ObjectComparisonService(IObjectComparisonService):
    def __init__(self):
        self.service_name = "ObjectComparisonService"
        self.logger = Logger()

    def find_unique_objects(self, detected_objects, reference_objects, match_threshold=10):
        if not detected_objects:
            return []

        if not reference_objects:
            return detected_objects

        ref_coords = np.array([[coord[0], coord[1]] for coord in reference_objects])
        kdtree = KDTree(ref_coords)

        unique_objects = []

        detected_coords = np.array([[obj["x"], obj["y"]] for obj in detected_objects])

        distances, _ = kdtree.query(detected_coords, k=1)

        for i, distance in enumerate(distances):
            if distance > match_threshold:
                unique_objects.append(detected_objects[i])

        return unique_objects