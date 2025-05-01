import os
import pytest
from unittest.mock import Mock, patch

from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase
from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase
from src.application.use_cases.process_image_use_case import ProcessImageUseCase
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter

def vcr_read_fix(original_read):
    def new_read(self, *args, **kwargs):
        if 'decode_content' in kwargs:
            kwargs.pop('decode_content')
        return original_read(self, *args, **kwargs)
    return new_read


original_vcr_read = vcr.stubs.VCRHTTPResponse.read
vcr.stubs.VCRHTTPResponse.read = vcr_read_fix(original_vcr_read)

# Оставшийся код без изменений
my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',
    decode_compressed_response=True
)

class TestApplicationIntegration:
    @pytest.fixture
    def setup_use_cases(self):
        detection_service = SepDetectionAdapter()
        detect_use_case = DetectObjectsUseCase(detection_service)

        parallel_service = ParallelProcessingService()
        process_use_case = ProcessImageUseCase(parallel_service)

        mock_astrometry = Mock()
        mock_astrometry.calibrate_image.return_value = {
            "job_id": 12345,
            "wcs_path": "tests/fixtures/test_wcs.fits",
            "rdls_path": "tests/fixtures/test_rdls.fits"
        }

        mock_catalog = Mock()
        mock_catalog.query_by_coordinates.return_value = []

        calibrate_use_case = CalibrateImageUseCase(mock_astrometry)
        verify_use_case = VerifyUnknownObjectsUseCase(mock_catalog)

        return {
            "detect_use_case": detect_use_case,
            "calibrate_use_case": calibrate_use_case,
            "verify_use_case": verify_use_case,
            "process_use_case": process_use_case,
            "mock_astrometry": mock_astrometry,
            "mock_catalog": mock_catalog
        }

    def test_process_image_workflow_integration(self, setup_use_cases, tmp_path):
        test_image = "tests/fixtures/test_star_field.jpg"

        os.makedirs(os.path.dirname(setup_use_cases["mock_astrometry"].calibrate_image.return_value["wcs_path"]),
                    exist_ok=True)

        with patch('astropy.wcs.WCS') as mock_wcs, \
             patch('astropy.io.fits.open') as mock_fits_open, \
             patch('src.infrastructure.utils.image_highlighter.ImageHighlighter'):

            mock_wcs_instance = mock_wcs.return_value
            mock_wcs_instance.all_pix2world.return_value = [[120.0, 40.0]]

            result = setup_use_cases["process_use_case"].execute(
                test_image,
                setup_use_cases["calibrate_use_case"],
                setup_use_cases["detect_use_case"],
                setup_use_cases["verify_use_case"]
            )

            setup_use_cases["mock_astrometry"].calibrate_image.assert_called_once_with(test_image)

            assert "wcs_path" in result
            assert "pixel_coords" in result, "Координаты пикселей должны быть в результате"

            setup_use_cases["mock_catalog"].query_by_coordinates.assert_called()