import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from src.infrastructure.service.object_classification_service import ObjectClassificationService


class TestObjectClassificationService:
    def setup_method(self):
        """Настройка среды для каждого теста"""
        self.catalog_service = Mock()
        self.service = ObjectClassificationService(self.catalog_service)
        self.test_wcs_path = "path/to/wcs.fits"
        self.test_pixel_coords = [(100, 200), (300, 400)]
        self.objects_data = {
            "wcs_path": self.test_wcs_path,
            "pixel_coords": self.test_pixel_coords
        }

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_objects_star(self, mock_fits_open):
        """Тест классификации звёздных объектов"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем первый запрос к каталогу (звезда)
            self.catalog_service.query_by_coordinates.return_value = [
                ('gaia', {'source_id': 123456789})]

            result = self.service.classify_objects(self.objects_data)

            assert "classified_objects" in result
            assert len(result["classified_objects"]) == 2
            assert result["classified_objects"][0]["class"] == "star"
            assert result["classified_objects"][0]["ra"] == 50.0
            assert result["classified_objects"][0]["dec"] == 30.0

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_objects_asteroid(self, mock_fits_open):
        """Тест классификации астероидов"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем запрос к каталогу (астероид)
            self.catalog_service.query_by_coordinates.return_value = [
                ('mpc_asteroids', {'name': 'Ceres'})]

            result = self.service.classify_objects(self.objects_data)

            assert "classified_objects" in result
            assert len(result["classified_objects"]) == 2
            assert result["classified_objects"][0]["class"] == "asteroid"

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_objects_comet(self, mock_fits_open):
        """Тест классификации комет"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем запрос к каталогу (комета)
            self.catalog_service.query_by_coordinates.return_value = [
                ('mpc_comets', {'name': 'Halley'})]

            result = self.service.classify_objects(self.objects_data)

            assert "classified_objects" in result
            assert len(result["classified_objects"]) == 2
            assert result["classified_objects"][0]["class"] == "comet"

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_objects_solar_system_body(self, mock_fits_open):
        """Тест классификации тел солнечной системы"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем запрос к каталогу (планета)
            self.catalog_service.query_by_coordinates.return_value = [
                ('solar_system', {'body': 'jupiter'})]

            result = self.service.classify_objects(self.objects_data)

            assert result["classified_objects"][0]["class"] == "jupiter"

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_objects_galaxy(self, mock_fits_open):
        """Тест классификации галактических объектов через SIMBAD"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        # Создаем мок-данные для результата SIMBAD
        simbad_result = MagicMock()
        colnames = ["OTYPE"]
        simbad_result.colnames = colnames
        # Должен быть индексируемым как массив
        simbad_result.__getitem__.side_effect = lambda idx: "G" if idx == 0 else None

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем запрос к каталогу (галактика)
            self.catalog_service.query_by_coordinates.return_value = [('simbad', simbad_result)]

            result = self.service.classify_objects(self.objects_data)

            assert result["classified_objects"][0]["class"] == "G"

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_classify_unknown_objects(self, mock_fits_open):
        """Тест классификации неизвестных объектов"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Пустой результат каталога - объект неизвестен
            self.catalog_service.query_by_coordinates.return_value = []

            result = self.service.classify_objects(self.objects_data)

            assert result["classified_objects"][0]["class"] == "unknown"

    def test_missing_required_data(self):
        """Тест обработки отсутствующих данных"""
        # Тест без пути к WCS файлу
        result = self.service.classify_objects({"pixel_coords": self.test_pixel_coords})
        assert "error" in result

        # Тест без координат пикселей
        result = self.service.classify_objects({"wcs_path": self.test_wcs_path})
        assert "error" in result

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_wcs_error_handling(self, mock_fits_open):
        """Тест обработки ошибок при работе с WCS"""
        mock_fits_open.side_effect = Exception("WCS file error")

        result = self.service.classify_objects(self.objects_data)

        assert "error" in result
        assert "WCS file error" in result["error"]

    @patch("src.infrastructure.service.object_classification_service.fits.open")
    def test_catalog_service_error_handling(self, mock_fits_open):
        """Тест обработки ошибок при запросе к каталогу"""
        # Настраиваем мок для WCS
        mock_wcs = Mock(spec=WCS)
        mock_wcs.all_pix2world.return_value = np.array([[50.0, 30.0]])
        mock_hdul = MagicMock()
        mock_fits_open.return_value.__enter__.return_value = mock_hdul
        mock_hdul_instance = MagicMock()
        mock_hdul_instance.header = "header_data"
        mock_hdul[0] = mock_hdul_instance

        with patch("src.infrastructure.service.object_classification_service.WCS", return_value=mock_wcs):
            # Настраиваем ошибку при запросе к каталогу
            self.catalog_service.query_by_coordinates.side_effect = Exception("Catalog error")

            result = self.service.classify_objects(self.objects_data)

            assert "error" in result