import pytest
from unittest.mock import Mock
from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase


class TestCalibrateImageUseCase:
    def setup_method(self):
        self.mock_astrometry_service = Mock()
        self.use_case = CalibrateImageUseCase(self.mock_astrometry_service)
        self.test_image_path = "test_image.jpg"

    def test_execute_success(self):
        expected_result = {
            "job_id": "12345",
            "wcs_path": "test_image_wcs.fits",
            "rdls_path": "test_image_rdls.rdls"
        }
        self.mock_astrometry_service.calibrate_image.return_value = expected_result

        result = self.use_case.execute(self.test_image_path)

        self.mock_astrometry_service.calibrate_image.assert_called_once_with(self.test_image_path)
        assert result == expected_result

    def test_execute_failure_none_result(self):
        self.mock_astrometry_service.calibrate_image.return_value = None

        result = self.use_case.execute(self.test_image_path)

        assert result is None

    def test_execute_exception(self):
        self.mock_astrometry_service.calibrate_image.side_effect = Exception("Test error")

        result = self.use_case.execute(self.test_image_path)

        assert result is None

    def test_process_success(self):
        expected_result = {
            "job_id": "12345",
            "wcs_path": "test_image_wcs.fits",
            "rdls_path": "test_image_rdls.rdls"
        }
        self.mock_astrometry_service.calibrate_image.return_value = expected_result
        data = {"image_path": self.test_image_path}

        result = self.use_case.process(data)

        assert result == expected_result

    def test_process_missing_image_path(self):
        data = {}

        result = self.use_case.process(data)

        assert "error" in result
        assert result["error"] == "The path to the image is missing"