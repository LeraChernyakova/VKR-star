from src.infrastructure.utils.logger import Logger


class DetectObjectsUseCase:
    def __init__(self, detection_service):
        self.service_name = "DetectObjectsUseCase"
        self.detection_service = detection_service
        self.logger = Logger()

    def execute(self, image_path):
        try:
            result = self.detection_service.detect_objects(image_path)

            if "error" in result:
                self.logger.error(self.service_name,f"Error while detect objects: {result['error']}")
                return result

            return result

        except Exception as e:
            self.logger.error(self.service_name,f"Error while detect objects: {str(e)}")
            return {"error": str(e)}

    def process(self, data):
        if "image_path" not in data:
            return {"error": "path to image missing"}
        return self.execute(data["image_path"])