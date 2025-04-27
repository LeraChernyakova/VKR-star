import pytest
from unittest.mock import Mock, patch
from src.application.use_cases.process_image_use_case import ProcessImageUseCase


class TestProcessImageUseCase:
    def setup_method(self):
        self.mock_parallel_service = Mock()
        self.use_case = ProcessImageUseCase(self.mock_parallel_service)
        self.test_image_path = "test_image.jpg"

        self.mock_astrometry_processor = Mock()
        self.mock_detection_processor = Mock()
        self.mock_comparison_processor = Mock()

    def test_execute_success(self):
        astrometry_result = {
            "wcs_path": "test_wcs.fits",
            "rdls_path": "test_rdls.rdls"
        }
        detection_result = {
            "pixel_coords": [(100, 200), (300, 400)],
            "flux": [1000.0, 2000.0]
        }

        self.mock_parallel_service.execute_parallel_tasks.return_value = {
            "astrometry": astrometry_result,
            "detection": detection_result
        }

        expected_final_result = {
            "truly_unknown": [(100, 200)],
            "visualization_path": "test_output.jpg"
        }
        self.mock_comparison_processor.process.return_value = expected_final_result

        result = self.use_case.execute(
            self.test_image_path,
            self.mock_astrometry_processor,
            self.mock_detection_processor,
            self.mock_comparison_processor
        )

        self.mock_parallel_service.execute_parallel_tasks.assert_called_once()
        call_args = self.mock_parallel_service.execute_parallel_tasks.call_args[0]
        assert call_args[0] == {"image_path": self.test_image_path}
        assert "astrometry" in call_args[1]
        assert "detection" in call_args[1]

        expected_combined_data = {
            "image_path": self.test_image_path,
            "wcs_path": "test_wcs.fits",
            "rdls_path": "test_rdls.rdls",
            "pixel_coords": [(100, 200), (300, 400)],
            "flux": [1000.0, 2000.0]
        }
        self.mock_comparison_processor.process.assert_called_once_with(expected_combined_data)

        assert result == expected_final_result

    def test_execute_parallel_service_error(self):
        error_msg = "Ошибка параллельной обработки"
        self.mock_parallel_service.execute_parallel_tasks.side_effect = Exception(error_msg)

        result = self.use_case.execute(
            self.test_image_path,
            self.mock_astrometry_processor,
            self.mock_detection_processor,
            self.mock_comparison_processor
        )

        assert "error" in result
        assert error_msg in result["error"]
        self.mock_comparison_processor.process.assert_not_called()

    def test_execute_comparison_processor_error(self):
        self.mock_parallel_service.execute_parallel_tasks.return_value = {
            "astrometry": {"wcs_path": "test_wcs.fits"},
            "detection": {"pixel_coords": [(100, 200)]}
        }

        error_msg = "Ошибка в процессоре сравнения"
        self.mock_comparison_processor.process.side_effect = Exception(error_msg)

        result = self.use_case.execute(
            self.test_image_path,
            self.mock_astrometry_processor,
            self.mock_detection_processor,
            self.mock_comparison_processor
        )

        assert "error" in result
        assert error_msg in result["error"]

    def test_execute_process_error_in_partial_result(self):
        self.mock_parallel_service.execute_parallel_tasks.return_value = {
            "astrometry": {"error": "Ошибка калибровки изображения"},
            "detection": {"pixel_coords": [(100, 200)]}
        }

        result = self.use_case.execute(
            self.test_image_path,
            self.mock_astrometry_processor,
            self.mock_detection_processor,
            self.mock_comparison_processor
        )

        expected_combined_data = {
            "image_path": self.test_image_path,
            "error": "Ошибка калибровки изображения",
            "pixel_coords": [(100, 200)]
        }
        self.mock_comparison_processor.process.assert_called_once_with(expected_combined_data)