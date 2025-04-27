import pytest
from unittest.mock import Mock
from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase


class TestDetectObjectsUseCase:
    def setup_method(self):
        self.mock_detection_service = Mock()
        self.use_case = DetectObjectsUseCase(self.mock_detection_service)
        self.test_image_path = "test_image.jpg"

    def test_execute_success(self):
        expected_result = {
            "pixel_coords": [(100, 200), (300, 400)],
            "flux": [1000.0, 2000.0]
        }
        self.mock_detection_service.detect_objects.return_value = expected_result

        result = self.use_case.execute(self.test_image_path)

        self.mock_detection_service.detect_objects.assert_called_once_with(self.test_image_path)
        assert result == expected_result
        assert len(result["pixel_coords"]) == 2

    def test_execute_error(self):
        error_message = "Ошибка обработки изображения"
        self.mock_detection_service.detect_objects.return_value = {"error": error_message}

        result = self.use_case.execute(self.test_image_path)

        assert "error" in result
        assert result["error"] == error_message

    def test_execute_exception(self):
        exception_message = "Неожиданная ошибка"
        self.mock_detection_service.detect_objects.side_effect = Exception(exception_message)

        result = self.use_case.execute(self.test_image_path)

        assert "error" in result
        assert exception_message in result["error"]

    def test_process_success(self):
        expected_result = {
            "pixel_coords": [(100, 200), (300, 400)],
            "flux": [1000.0, 2000.0]
        }
        self.mock_detection_service.detect_objects.return_value = expected_result
        data = {"image_path": self.test_image_path}

        result = self.use_case.process(data)

        self.mock_detection_service.detect_objects.assert_called_once_with(self.test_image_path)
        assert result == expected_result

    def test_process_missing_image_path(self):
        data = {}

        result = self.use_case.process(data)

        assert "error" in result
        assert result["error"] == "Отсутствует путь к изображению"
        self.mock_detection_service.detect_objects.assert_not_called()