import pytest
import vcr
import os

from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase

my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',
    match_on=['uri', 'method'],
)


class TestAstrometryIntegration:
    @pytest.fixture
    def astrometry_adapter(self):
        api_key = "lyjwakywqahzzjvj"
        return AstrometryNetAdapter(api_key)

    @my_vcr.use_cassette('astrometry_login.yaml')
    def test_astrometry_login(self, astrometry_adapter):
        result = astrometry_adapter.login()
        assert result["status"] == "success"
        assert astrometry_adapter.session is not None

    @my_vcr.use_cassette('astrometry_calibration.yaml')
    def test_calibrate_image_use_case_integration(self, astrometry_adapter, tmp_path):
        calibrate_use_case = CalibrateImageUseCase(astrometry_adapter)

        test_image = "tests/fixtures/test_star_field.jpg"

        result = calibrate_use_case.execute(test_image)

        assert result is not None
        assert "job_id" in result
        assert "wcs_path" in result
        assert "rdls_path" in result
        assert os.path.exists(result["wcs_path"])