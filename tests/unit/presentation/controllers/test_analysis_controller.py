import pytest
from unittest.mock import Mock, patch
from src.presentation.controllers.analysis_controller import AnalysisController


class TestAnalysisController:
    def setup_method(self):
        """Настройка окружения перед каждым тестом"""
        self.select_image_use_case = Mock()
        self.calibrate_image_use_case = Mock()
        self.detect_objects_use_case = Mock()
        self.verify_objects_use_case = Mock()
        self.process_image_use_case = Mock()

        self.controller = AnalysisController(
            self.select_image_use_case,
            self.calibrate_image_use_case,
            self.detect_objects_use_case,
            self.verify_objects_use_case,
            self.process_image_use_case
        )

        self.test_image_path = "/path/to/test_image.jpg"
        self.test_wcs_path = "/path/to/test_wcs.fits"

    def test_select_image_success(self):
        """Тест успешного выбора изображения"""
        self.select_image_use_case.execute.return_value = self.test_image_path

        result = self.controller.select_image()

        self.select_image_use_case.execute.assert_called_once()
        assert result == self.test_image_path

    def test_select_image_none(self):
        """Тест отмены выбора изображения"""
        self.select_image_use_case.execute.return_value = None

        result = self.controller.select_image()

        self.select_image_use_case.execute.assert_called_once()
        assert result is None

    def test_analyze_image_success(self):
        """Тест успешного анализа изображения"""
        # Подготовка данных для тестов
        process_result = {
            "image_path": self.test_image_path,
            "wcs_path": self.test_wcs_path,
            "pixel_coords": [(100, 200), (300, 400)]
        }

        verification_result = {
            "truly_unknown": [(100, 200)],
            "truly_unknown_coords": [{"pixel_x": 100, "pixel_y": 200, "ra": 50.0, "dec": 30.0}],
            "visualization_path": "/path/to/output.jpg"
        }

        # Настройка моков
        self.process_image_use_case.execute.return_value = process_result
        self.verify_objects_use_case.execute.return_value = verification_result

        # Вызов тестируемого метода
        result = self.controller.analyze_image(self.test_image_path)

        # Проверки
        self.process_image_use_case.execute.assert_called_once_with(
            self.test_image_path,
            self.calibrate_image_use_case,
            self.detect_objects_use_case,
            self.verify_objects_use_case
        )

        self.verify_objects_use_case.execute.assert_called_once_with(
            self.test_image_path,
            self.test_wcs_path,
            [(100, 200), (300, 400)]
        )

        # Проверка содержимого результата
        assert "truly_unknown" in result
        assert "visualization_path" in result
        assert result["truly_unknown"] == [(100, 200)]
        assert result["visualization_path"] == "/path/to/output.jpg"

    def test_analyze_image_process_error(self):
        """Тест обработки ошибки в процессе анализа"""
        # Настройка мока для возврата ошибки
        error_result = {"error": "Произошла ошибка при обработке"}
        self.process_image_use_case.execute.return_value = error_result

        # Вызов тестируемого метода
        result = self.controller.analyze_image(self.test_image_path)

        # Проверки
        assert result == error_result
        self.verify_objects_use_case.execute.assert_not_called()

    def test_analyze_image_missing_data(self):
        """Тест обработки отсутствия необходимых данных"""
        # Настройка мока для возврата неполных данных
        incomplete_result = {
            "image_path": self.test_image_path,
            # Отсутствуют wcs_path и pixel_coords
        }

        self.process_image_use_case.execute.return_value = incomplete_result

        # Вызов тестируемого метода
        result = self.controller.analyze_image(self.test_image_path)

        # Проверки
        assert "error" in result
        assert "Не удалось получить необходимые данные" in result["error"]
        self.verify_objects_use_case.execute.assert_not_called()

    def test_analyze_image_exception(self):
        """Тест обработки исключения"""
        # Настройка мока для генерации исключения
        self.process_image_use_case.execute.side_effect = Exception("Непредвиденная ошибка")

        # Вызов тестируемого метода
        result = self.controller.analyze_image(self.test_image_path)

        # Проверки
        assert "error" in result
        assert "Непредвиденная ошибка" in result["error"]
        self.verify_objects_use_case.execute.assert_not_called()

    def test_analyze_image_verify_error(self):
        """Тест обработки ошибки в процессе верификации объектов"""
        # Подготовка данных
        process_result = {
            "image_path": self.test_image_path,
            "wcs_path": self.test_wcs_path,
            "pixel_coords": [(100, 200), (300, 400)]
        }

        verification_error = {"error": "Ошибка верификации"}

        # Настройка моков
        self.process_image_use_case.execute.return_value = process_result
        self.verify_objects_use_case.execute.return_value = verification_error

        # Вызов тестируемого метода
        result = self.controller.analyze_image(self.test_image_path)

        # Проверки
        assert "error" in result
        assert result["error"] == "Ошибка верификации"