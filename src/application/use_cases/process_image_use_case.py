from src.infrastructure.utils.logger import Logger


class ProcessImageUseCase:
    def __init__(self, parallel_processing_service):
        self.service_name = "ProcessImageUseCase"
        self.parallel_service = parallel_processing_service
        self.logger = Logger()

    def execute(self, image_path, astrometry_processor, detection_processor, comparison_processor):
        try:
            self.logger.info(self.service_name,f"Starting image processing for {image_path}")

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

            self.logger.info(self.service_name,"Running comparison process")
            final_result = comparison_processor.process(combined_data)

            return final_result

        except Exception as e:
            self.logger.error(self.service_name,"ProcessImageUseCase. Error in image processing workflow: {str(e)}")
            return {"error": str(e)}