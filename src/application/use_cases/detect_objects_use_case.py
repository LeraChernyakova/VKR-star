from src.infrastructure.utils.logger import Logger

class DetectObjectsUseCase:
    def __init__(self, detection_service):
        self.service_name = "DetectObjectsUseCase"
        self.detection_service = detection_service
        self.logger = Logger()

    def execute(self, image_path):
        try:
            self.logger.info(self.service_name,f"Запуск обнаружения объектов на изображении: {image_path}")
            result = self.detection_service.detect_objects(image_path)

            if "error" in result:
                self.logger.error(self.service_name,f"Ошибка при обнаружении объектов: {result['error']}")
                return result

            self.logger.info(self.service_name,f"Обнаружено объектов: {len(result.get('pixel_coords', []))}")
            return result

        except Exception as e:
            self.logger.error(self.service_name,f"Ошибка при обнаружении объектов: {str(e)}")
            return {"error": str(e)}

    def process(self, data):
        if "image_path" not in data:
            return {"error": "Отсутствует путь к изображению"}
        return self.execute(data["image_path"])