import numpy as np

from scipy.spatial import cKDTree

from src.domain.interfaces.object_comparison_service import IObjectComparisonService
from src.infrastructure.utils.logger import Logger


class ObjectComparisonService(IObjectComparisonService):
    def __init__(self):
        self.service_name = "ObjectComparisonService"
        self.logger = Logger()

    def find_unique_objects(self, detected_objects, reference_objects, match_threshold=10):
        if reference_objects:
            ref_coords = np.array(reference_objects)
            tree = cKDTree(ref_coords)

            det_coords = np.array([(o['x'], o['y']) for o in detected_objects])
            dists, _ = tree.query(det_coords, distance_upper_bound=match_threshold)

            unique = [obj for obj, dist in zip(detected_objects, dists) if dist > match_threshold]
        else:
            unique = detected_objects[:]

        return unique