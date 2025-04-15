class AnalysisController:
    def __init__(self, find_unknown_objects_use_case):
        self.find_unknown_objects = find_unknown_objects_use_case

    def analyze_image(self, image_path):
        try:
            unknown_objects = self.find_unknown_objects.execute(image_path)

            # Подготовка результата для отображения
            result = {
                "image_path": image_path,
                "unknown_objects": unknown_objects,
                "count": len(unknown_objects)
            }

            return result
        except Exception as e:
            # Обработка ошибок
            return {"error": str(e)}