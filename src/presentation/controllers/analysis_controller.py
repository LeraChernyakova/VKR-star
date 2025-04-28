import os

from src.infrastructure.utils.image_highlighter import ImageHighlighter
from src.infrastructure.service.object_comparison_service import ObjectComparisonService

class AnalysisController:
    def __init__(self, select_image_use_case, calibrate_image_use_case,
                 detect_objects_use_case, verify_objects_use_case, process_image_use_case):
        self.select_image_use_case = select_image_use_case
        self.calibrate_image_use_case = calibrate_image_use_case
        self.detect_objects_use_case = detect_objects_use_case
        self.verify_objects_use_case = verify_objects_use_case
        self.process_image_use_case = process_image_use_case

    def select_image(self):
        return self.select_image_use_case.execute()

    def analyze_image(self, image_path):
        try:
            result = self.process_image_use_case.execute(
                image_path,
                self.calibrate_image_use_case,
                self.detect_objects_use_case
            )

            sep_result = result.get("detection", {})
            astrometry_result = result.get("astrometry", {})

            sep_coords = sep_result.get("pixel_coords", [])
            astro_coords = astrometry_result.get("pixel_coords", [])
            wcs = astrometry_result.get("wcs")

            comparison_service = ObjectComparisonService()
            unique_coords = comparison_service.find_unique_objects(sep_coords, astro_coords, match_threshold=10)

            print(unique_coords)

            result = self.verify_objects_use_case.execute(image_path, unique_coords, wcs)

            return result

        except Exception as e:
            return {"error": str(e)}