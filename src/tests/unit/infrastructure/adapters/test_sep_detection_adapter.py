import pytest
from unittest.mock import patch, Mock, MagicMock
import numpy as np
import sep
from PIL import Image
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter


class TestSepDetectionAdapter:
    def setup_method(self):
        """Настройка тестового окружения перед каждым тестом"""
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
        """Тест успешного обнаружения объектов"""
        # Настройка моков
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        # Мок для numpy array
        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        # Мок для фона
        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        # Мок для извлеченных объектов
        mock_objects = np.array([(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)],
                                dtype=[('x', float), ('y', float)])
        mock_extract.return_value = mock_objects

        # Мок для потоков объектов
        mock_flux = np.array([100.0, 200.0, 50.0])
        mock_flux_err = np.array([1.0, 2.0, 0.5])
        mock_flag = np.array([0, 0, 0])
        mock_sum_circle.return_value = (mock_flux, mock_flux_err, mock_flag)

        # Мок для медианы потока
        mock_median.return_value = 100.0  # Медиана 100, порог 30 (100 * 0.3)

        # Выполнение метода
        result = self.adapter.detect_objects(self.test_image_path)

        # Проверки
        mock_image_open.assert_called_once_with(self.test_image_path)
        mock_extract.assert_called_once()
        mock_sum_circle.assert_called_once()

        # Проверка результата
        assert "objects" in result
        assert "pixel_coords" in result
        assert "flux" in result

        # Должны быть найдены только 2 объекта с потоком выше порога (100 * 0.3 = 30)
        # 100.0 и 200.0 выше порога, 50.0 ниже
        assert len(result["pixel_coords"]) == 2

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    def test_detect_objects_image_error(self, mock_image_open):
        """Тест обработки ошибки при открытии изображения"""
        # Настройка мока для вызова исключения
        mock_image_open.side_effect = Exception("Cannot open image")

        # Выполнение метода
        result = self.adapter.detect_objects(self.test_image_path)

        # Проверка результата
        assert "error" in result
        assert "Cannot open image" in result["error"]

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    def test_detect_objects_sep_error(self, mock_background, mock_np_array, mock_image_open):
        """Тест обработки ошибки при обработке изображения в SEP"""
        # Настройка моков
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        # Мок для вызова исключения при создании объекта Background
        mock_background.side_effect = Exception("SEP processing error")

        # Выполнение метода
        result = self.adapter.detect_objects(self.test_image_path)

        # Проверка результата
        assert "error" in result
        assert "SEP processing error" in result["error"]

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    def test_detect_objects_no_objects_found(self, mock_sum_circle, mock_extract, mock_background, mock_np_array,
                                             mock_image_open):
        """Тест случая, когда объекты не обнаружены"""
        # Настройка моков
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        # Пустой массив объектов
        empty_objects = np.array([], dtype=[('x', float), ('y', float)])
        mock_extract.return_value = empty_objects

        # Пустые массивы потоков
        mock_sum_circle.return_value = (np.array([]), np.array([]), np.array([]))

        # Выполнение метода
        result = self.adapter.detect_objects(self.test_image_path)

        # Проверка результата
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
        """Тест случая, когда все обнаруженные объекты имеют поток ниже порога"""
        # Настройка моков
        mock_image = MagicMock()
        mock_image_open.return_value.convert.return_value = mock_image

        mock_data = np.zeros((100, 100), dtype=np.float32)
        mock_np_array.return_value = mock_data

        mock_bkg = MagicMock()
        mock_bkg.globalrms = 1.0
        mock_background.return_value = mock_bkg

        # Массив объектов
        mock_objects = np.array([(10.0, 20.0), (30.0, 40.0)], dtype=[('x', float), ('y', float)])
        mock_extract.return_value = mock_objects

        # Низкий поток для всех объектов
        mock_flux = np.array([10.0, 15.0])
        mock_flux_err = np.array([1.0, 1.5])
        mock_flag = np.array([0, 0])
        mock_sum_circle.return_value = (mock_flux, mock_flux_err, mock_flag)

        # Высокая медиана для порога
        mock_median.return_value = 100.0  # Порог 100 * 0.3 = 30

        # Выполнение метода
        result = self.adapter.detect_objects(self.test_image_path)

        # Проверка результата
        assert "objects" in result
        assert "pixel_coords" in result
        assert "flux" in result
        # Все объекты должны быть отфильтрованы, так как их поток ниже порога
        assert len(result["pixel_coords"]) == 0

    @patch("src.infrastructure.adapters.sep_detection_adapter.Image.open")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.array")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.Background")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.extract")
    @patch("src.infrastructure.adapters.sep_detection_adapter.sep.sum_circle")
    @patch("src.infrastructure.adapters.sep_detection_adapter.np.median")
    def test_detect_objects_extract_parameters(self, mock_median, mock_sum_circle, mock_extract, mock_background,
                                               mock_np_array, mock_image_open):
        """Тест параметров, передаваемых в функцию extract"""
        # Настройка моков
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

        # Выполнение метода
        self.adapter.detect_objects(self.test_image_path)

        # Проверка параметров, переданных в sep.extract
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args

        # Проверка наличия важных параметров в вызове extract
        assert "thresh" in kwargs
        assert "minarea" in kwargs
        assert "deblend_nthresh" in kwargs
        assert "deblend_cont" in kwargs
        assert kwargs["thresh"] == 5.0
        assert kwargs["minarea"] == 10