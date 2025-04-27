from src.infrastructure.utils.logger import Logger


class ProcessImageUseCase:
    def __init__(self, parallel_processing_service, object_comparison_service):
        self.service_name = "ProcessImageUseCase"
        self.parallel_service = parallel_processing_service
        self.comparison_service = object_comparison_service
        self.logger = Logger()

    def execute(self, image_path, astrometry_processor, detection_processor):
        try:
            initial_data = {"image_path": image_path}

            processors = {
                "astrometry": astrometry_processor,
                "detection": detection_processor
            }

            results = self.parallel_service.execute_parallel_tasks(
                initial_data, processors
            )

            combined_data = initial_data.copy()
            for result_key, result_data in results.items():
                if isinstance(result_data, dict):
                    for key, value in result_data.items():
                        combined_data[key] = value

            detected_objects = combined_data.get("pixel_coords", [])

            reference_objects = []
            if "astrometry" in results and isinstance(results["astrometry"], dict):
                # Если в результатах калибровки есть ключ с координатами эталонных объектов
                reference_objects = results["astrometry"].get("reference_stars", [])

            final_result = self.comparison_service.process(combined_data)

            return final_result

        except Exception as e:
            self.logger.error(self.service_name,"Error in image processing: {str(e)}")
            return {"error": str(e)}