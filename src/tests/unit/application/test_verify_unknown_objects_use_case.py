import pytest
from unittest.mock import Mock, patch, mock_open
import os
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase


class TestVerifyUnknownObjectsUseCase:
    def setup_method(self):
        self.mock_catalog_service = Mock()
        self.use_case = VerifyUnknownObjectsUseCase(self.mock_catalog_service)
        self.test_image_path = "test_image.jpg"
        self.test_wcs_path = "test_image_wcs.fits"
        self.test_coordinates = [(100, 200), (300, 400), (500, 600)]

    @patch('astropy.wcs.WCS')
    @patch('astropy.io.fits.open')
    def test_execute_all_unknown_objects(self, mock_fits_open, mock_wcs):
        mock_wcs_instance = Mock()
        mock_wcs_instance.all_pix2world.side_effect = lambda coords, origin: [
            [10.0 + coord[0] / 100, 20.0 + coord[1] / 100] for coord in coords
        ]
        mock_wcs.return_value = mock_wcs_instance

        mock_hdul = Mock()
        mock_fits_open.return_value.__enter__.return_value = [mock_hdul]
        mock_hdul.header = {}

        self.mock_catalog_service.query_by_coordinates.return_value = []

        with patch('src.infrastructure.utils.image_highlighter.ImageHighlighter') as mock_highlighter:
            mock_highlighter_instance = Mock()
            mock_highlighter.return_value = mock_highlighter_instance

            result = self.use_case.execute(
                self.test_image_path,
                self.test_wcs_path,
                self.test_coordinates
            )

        assert len(result["truly_unknown"]) == 3
        assert len(result["truly_unknown_coords"]) == 3
        self.mock_catalog_service.query_by_coordinates.assert_called()
        mock_highlighter_instance.highlight_points.assert_called_once()
        mock_highlighter_instance.save.assert_called_once()
        assert "visualization_path" in result

    @patch('astropy.wcs.WCS')
    @patch('astropy.io.fits.open')
    def test_execute_all_known_objects(self, mock_fits_open, mock_wcs):
        mock_wcs_instance = Mock()
        mock_wcs_instance.all_pix2world.side_effect = lambda coords, origin: [
            [10.0 + coord[0] / 100, 20.0 + coord[1] / 100] for coord in coords
        ]
        mock_wcs.return_value = mock_wcs_instance

        mock_hdul = Mock()
        mock_fits_open.return_value.__enter__.return_value = [mock_hdul]
        mock_hdul.header = {}

        catalog_result = [("gaia", "some_gaia_data")]
        self.mock_catalog_service.query_by_coordinates.return_value = catalog_result

        with patch('src.infrastructure.utils.image_highlighter.ImageHighlighter') as mock_highlighter:
            result = self.use_case.execute(
                self.test_image_path,
                self.test_wcs_path,
                self.test_coordinates
            )

        assert len(result["truly_unknown"]) == 0
        assert len(result["truly_unknown_coords"]) == 0
        self.mock_catalog_service.query_by_coordinates.assert_called()
        assert "visualization_path" not in result

    @patch('astropy.wcs.WCS')
    @patch('astropy.io.fits.open')
    def test_execute_mixed_objects(self, mock_fits_open, mock_wcs):
        mock_wcs_instance = Mock()
        mock_wcs_instance.all_pix2world.side_effect = lambda coords, origin: [
            [10.0 + coord[0] / 100, 20.0 + coord[1] / 100] for coord in coords
        ]
        mock_wcs.return_value = mock_wcs_instance

        mock_hdul = Mock()
        mock_fits_open.return_value.__enter__.return_value = [mock_hdul]
        mock_hdul.header = {}

        self.mock_catalog_service.query_by_coordinates.side_effect = [
            [("gaia", "data")],
            [("simbad", "data")],
            []
        ]

        with patch('src.infrastructure.utils.image_highlighter.ImageHighlighter') as mock_highlighter:
            mock_highlighter_instance = Mock()
            mock_highlighter.return_value = mock_highlighter_instance

            result = self.use_case.execute(
                self.test_image_path,
                self.test_wcs_path,
                self.test_coordinates
            )

        assert len(result["truly_unknown"]) == 1
        assert result["truly_unknown"][0] == self.test_coordinates[2]
        assert len(result["truly_unknown_coords"]) == 1
        mock_highlighter_instance.highlight_points.assert_called_once()
        mock_highlighter_instance.save.assert_called_once()
        assert "visualization_path" in result

    @patch('astropy.wcs.WCS')
    @patch('astropy.io.fits.open')
    def test_execute_exception(self, mock_fits_open, mock_wcs):
        mock_fits_open.side_effect = Exception("Test WCS error")

        result = self.use_case.execute(
            self.test_image_path,
            self.test_wcs_path,
            self.test_coordinates
        )

        assert "error" in result
        assert "Test WCS error" in result["error"]

    def test_process_successful(self):
        data = {
            "image_path": self.test_image_path,
            "wcs_path": self.test_wcs_path,
            "pixel_coords": self.test_coordinates
        }

        with patch.object(self.use_case, 'execute') as mock_execute:
            mock_execute.return_value = {"truly_unknown": []}

            result = self.use_case.process(data)

            mock_execute.assert_called_once_with(
                self.test_image_path,
                self.test_wcs_path,
                self.test_coordinates
            )
            assert result == {"truly_unknown": []}

    def test_process_missing_data(self):
        data = {"image_path": self.test_image_path}

        result = self.use_case.process(data)

        assert "error" in result
        assert "Недостаточно данных" in result["error"]