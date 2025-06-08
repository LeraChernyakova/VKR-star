import os
from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter


class ProcessImageUseCase:
    def __init__(self, parallel_processing_service, verify_unknown_objects_use_case):
        self.service_name = "ProcessImageUseCase"
        self.parallel_service = parallel_processing_service
        self.verify_objects_use_case = verify_unknown_objects_use_case
        self.logger = Logger()

    def execute(self, image_path, status_callback=None):
        try:
            initial_data = {"image_path": image_path}

            results = self.parallel_service.execute_parallel_tasks(initial_data)

            sep_result = results.get("detection", {})
            astrometry_result = results.get("astrometry", {})

            sep_coords = sep_result.get("pixel_coords", [])
            astro_coords = astrometry_result.get("pixel_coords", [])
            wcs = astrometry_result.get("wcs")

            if wcs:
                if status_callback:
                    status_callback("Поиск данных в каталогах...", "blue")

                verify_result = self.verify_objects_use_case.execute(
                    image_path, sep_coords, astro_coords, wcs
                )

                unknown = verify_result.get("unknown_objects", [])
                points = [(o.get("x"), o.get("y")) for o in unknown]

                highlighter = ImageHighlighter(image_path)
                highlighter.highlight_points(points, radius=8, color="yellow")
                base, ext = os.path.splitext(image_path)
                vis_path = f"{base}_highlighted{ext}"
                highlighter.save(vis_path)

                results["unknown_objects"] = unknown
                results["visualization_path"] = vis_path

            return results

        except Exception as e:
            self.logger.error(self.service_name, f"Error in image processing: {str(e)}")
            return {"error": str(e)}