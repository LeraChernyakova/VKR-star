# tests/integration/presentation/test_controller_integration.py

import pytest
from unittest.mock import Mock, patch
import os

from src.presentation.controllers.analysis_controller import AnalysisController
from src.application.use_cases.process_image_use_case import ProcessImageUseCase
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService


class TestControllerIntegration:
    @pytest.fixture
    def setup_controller(self):
        # Создаем реальный ParallelProcessingService
        parallel_service = ParallelProcessingService()
        process_use_case = ProcessImageUseCase(parallel_service)

        # Создаем моки для остальных use cases
        mock_select = Mock()
        mock_calibrate = Mock()
        mock_detect = Mock()
        mock_verify = Mock()

        # Настраиваем нужное поведение
        mock_select.execute.return_value = "test_image.jpg"
        mock_calibrate.process.return_value = {
            "wcs_path": "tests/fixtures/test_wcs.fits",
            "job_id": 12345
        }
        mock_detect.process.return_value = {
            "pixel_coords": [(100, 100), (200, 200)]
        }
        mock_verify.execute.return_value = {
            "truly_unknown": [(100, 100)],
            "truly_unknown_coords": [{"ra": 120.5, "dec": 45.0}],
            "visualization_path": "tests/fixtures/test_visualization.jpg"
        }

        # Создаем контроллер
        controller = AnalysisController(
            mock_select, mock_calibrate, mock_detect, mock_verify, process_use_case
        )

        return {
            "controller": controller,
            "mock_select": mock_select,
            "mock_calibrate": mock_calibrate,
            "mock_detect": mock_detect,
            "mock_verify": mock_verify,
            "process_use_case": process_use_case
        }

    def test_controller_analyze_image_integration(self, setup_controller):
        # Создаем патчи для предотвращения реальных вызовов
        with patch.object(setup_controller["process_use_case"], "execute") as mock_process_execute:
            # Настраиваем мок процесса
            mock_process_execute.return_value = {
                "image_path": "test_image.jpg",
                "wcs_path": "tests/fixtures/test_wcs.fits",
                "pixel_coords": [(100, 100), (200, 200)]
            }

            # Вызываем метод контроллера
            result = setup_controller["controller"].analyze_image("test_image.jpg")

            # Проверяем, что process_use_case.execute был вызван с правильными параметрами
            mock_process_execute.assert_called_once_with(
                "test_image.jpg",
                setup_controller["mock_calibrate"],
                setup_controller["mock_detect"],
                setup_controller["mock_verify"]
            )

            # Проверяем, что verify_use_case.execute был вызван
            setup_controller["mock_verify"].execute.assert_called_once()

            # Проверяем результат
            assert "truly_unknown_coords" in result