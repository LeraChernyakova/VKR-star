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

            return results

        except Exception as e:
            self.logger.error(self.service_name,"Error in image processing: {str(e)}")
            return {"error": str(e)}