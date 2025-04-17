from src.infrastructure.utils.logger import Logger


class CalibrateImageUseCase:
    def __init__(self, astrometry_service):
        self.service_name = "CalibrateImageUseCase"
        self.astrometry_service = astrometry_service
        self.logger = Logger()

    def execute(self, image_path):
        try:
            self.logger.info(self.service_name,f"Astrometry calibrate start")
            result = self.astrometry_service.calibrate_image(image_path)

            if result is None:
                self.logger.error(self.service_name,"Image calibration failed")
                return None

            self.logger.info(self.service_name,f"Image calibration success")
            return result

        except Exception as e:
            self.logger.error(self.service_name,f"Error while calibrate: {str(e)}")
            return None

    def process(self, data):
        if "image_path" not in data:
            return {"error": "The path to the image is missing"}
        return self.execute(data["image_path"])