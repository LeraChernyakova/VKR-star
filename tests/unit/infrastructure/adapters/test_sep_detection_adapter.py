import pytest
from unittest.mock import patch, Mock, MagicMock
import numpy as np
import sep
from PIL import Image
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter


class TestSepDetectionAdapter:
    def setup_method(self):
        self.adapter = SepDetectionAdapter()
        self.test_image_path = "test_image.jpg"

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.median")
    def test_detect_objects_success(self, mock_median, mock_sum_circle, mock_extract, mock_background, mock_np_array,
                                    mock_image_open):
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        mock_objects = np.array([(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)],
                                dtype=[('x', float), ('y', float)])
        mock_extract.return_value = mock_objects

        mock_flux = np.array([100.0, 200.0, 50.0])
        mock_flux_err = np.array([1.0, 2.0, 0.5])
        mock_flag = np.array([0, 0, 0])
        mock_sum_circle.return_value = (mock_flux, mock_flux_err, mock_flag)

        mock_median.return_value = 100.0

        result = self.adapter.detect_objects(self.test_image_path)

        mock_image_open.assert_called_once_with(self.test_image_path)
        mock_extract.assert_called_once()
        mock_sum_circle.assert_called_once()

        assert "objects" in result
        assert "pixel_coords" in result
        assert "flux" in result

        assert len(result["pixel_coords"]) == 2

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    def test_detect_objects_image_error(self, mock_image_open):
        mock_image_open.side_effect = Exception("Cannot open image")

        result = self.adapter.detect_objects(self.test_image_path)

        assert "error" in result
        assert "Cannot open image" in result["error"]

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    def test_detect_objects_sep_error(self, mock_background, mock_np_array, mock_image_open):
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_background.side_effect = Exception("SEP processing error")

        result = self.adapter.detect_objects(self.test_image_path)

        assert "error" in result
        assert "SEP processing error" in result["error"]

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    def test_detect_objects_no_objects_found(self, mock_sum_circle, mock_extract, mock_background, mock_np_array,
                                             mock_image_open):
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        empty_objects = np.array([], dtype=[('x', float), ('y', float)])
        mock_extract.return_value = empty_objects

        mock_sum_circle.return_value = (np.array([]), np.array([]), np.array([]))

        result = self.adapter.detect_objects(self.test_image_path)

        assert "objects" in result
        assert "pixel_coords" in result
        assert "flux" in result
        assert len(result["pixel_coords"]) == 0

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.median")
    def test_detect_objects_all_below_threshold(self, mock_median, mock_sum_circle, mock_extract, mock_background,
                                                mock_np_array, mock_image_open):
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        mock_objects = np.array([(10.0, 20.0), (30.0, 40.0)], dtype=[('x', float), ('y', float)])
        mock_extract.return_value = mock_objects

        mock_flux = np.array([10.0, 15.0])
        mock_flux_err = np.array([1.0, 1.5])
        mock_flag = np.array([0, 0])
        mock_sum_circle.return_value = (mock_flux, mock_flux_err, mock_flag)

        mock_median.return_value = 100.0

        result = self.adapter.detect_objects(self.test_image_path)

        assert "objects" in result
        assert "pixel_coords" in result
        assert "flux" in result
        assert len(result["pixel_coords"]) == 0

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.median")
    def test_detect_objects_extract_parameters(self, mock_median, mock_sum_circle, mock_extract, mock_background,
                                               mock_np_array, mock_image_open):
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg
        mock_data_sub = mock_data - mock_bkg

        mock_objects = np.array([(10.0, 20.0)], dtype=[('x', float), ('y', float)])
        mock_extract.return_value = mock_objects

        mock_flux = np.array([100.0])
        mock_flux_err = np.array([1.0])
        mock_flag = np.array([0])
        mock_sum_circle.return_value = (mock_flux, mock_flux_err, mock_flag)

        mock_median.return_value = 50.0

        self.adapter.detect_objects(self.test_image_path)

        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args

        assert "thresh" in kwargs
        assert "minarea" in kwargs
        assert "deblend_nthresh" in kwargs
        assert "deblend_cont" in kwargs
        assert kwargs["thresh"] == 5.0
        assert kwargs["minarea"] == 10