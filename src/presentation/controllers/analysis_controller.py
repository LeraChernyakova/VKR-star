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
                self.detect_objects_use_case,
                self.verify_objects_use_case
            )

            if "error" in result:
                return result

            if "wcs_path" not in result or "pixel_coords" not in result:
                return {"error": "Не удалось получить необходимые данные из изображения"}

            verification_result = self.verify_objects_use_case.execute(
                result["image_path"],
                result["wcs_path"],
                result["pixel_coords"]
            )

            result.update(verification_result)

            return result

        except Exception as e:
            return {"error": str(e)}