import threading

from src.infrastructure.utils.logger import Logger


class ParallelProcessingService:
    def __init__(self, calibrate_image_use_case, detect_objects_use_case):
        self.service_name = "ParallelProcessingService"
        self.calibrate_image_use_case = calibrate_image_use_case
        self.detect_objects_use_case = detect_objects_use_case
        self.logger = Logger()

    def execute_parallel_tasks(self, data):
        results = {}
        threads = []

        processors = {
            "astrometry": self.calibrate_image_use_case,
            "detection": self.detect_objects_use_case
        }

        for name, processor in processors.items():
            thread = threading.Thread(
                target=self._execute_processor,
                args=(name, processor, data.copy(), results),
                daemon=True
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return results

    def _execute_processor(self, name, processor, data, results):
        try:
            result = processor.process(data)
            results[name] = result
        except Exception as e:
            self.logger.error(self.service_name,f"Error in processor {name}: {str(e)}")
            results[name] = {"error": str(e)}