import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from src.infrastructure.utils.image_highlighter import ImageHighlighter


class TestImageHighlighter:
    def setup_method(self):
        """Настройка среды для каждого теста"""
        self.test_image_path = "test_image.jpg"
        self.test_output_path = "test_output.jpg"

    @patch("src.infrastructure.utils.image_highlighter.Image")
    @patch("src.infrastructure.utils.image_highlighter.ImageDraw")
    def test_initialization(self, mock_image_draw, mock_image):
        """Тест инициализации класса"""
        # Настройка моков
        mock_image_instance = MagicMock()
        mock_image.open.return_value = mock_image_instance
        mock_image_instance.convert.return_value = mock_image_instance

        mock_draw = MagicMock()
        mock_image_draw.Draw.return_value = mock_draw

        # Создание объекта
        highlighter = ImageHighlighter(self.test_image_path)

        # Проверки
        mock_image.open.assert_called_once_with(self.test_image_path)
        mock_image_instance.convert.assert_called_once_with("RGB")
        mock_image_draw.Draw.assert_called_once_with(mock_image_instance)
        assert highlighter.image == mock_image_instance
        assert highlighter.draw == mock_draw

    @patch("src.infrastructure.utils.image_highlighter.Image")
    @patch("src.infrastructure.utils.image_highlighter.ImageDraw")
    def test_highlight_single_point(self, mock_image_draw, mock_image):
        """Тест выделения одной точки на изображении"""
        # Настройка моков
        mock_image_instance = MagicMock()
        mock_image.open.return_value = mock_image_instance
        mock_image_instance.convert.return_value = mock_image_instance

        mock_draw = MagicMock()
        mock_image_draw.Draw.return_value = mock_draw

        # Создание объекта и вызов метода
        highlighter = ImageHighlighter(self.test_image_path)
        highlighter.highlight_points([(100, 200)], radius=10, color="red")

        # Проверка вызова метода рисования эллипса с правильными параметрами
        mock_draw.ellipse.assert_called_once_with([90, 190, 110, 210], outline="red", width=2)

    @patch("src.infrastructure.utils.image_highlighter.Image")
    @patch("src.infrastructure.utils.image_highlighter.ImageDraw")
    def test_highlight_multiple_points(self, mock_image_draw, mock_image):
        """Тест выделения нескольких точек на изображении"""
        # Настройка моков
        mock_image_instance = MagicMock()
        mock_image.open.return_value = mock_image_instance
        mock_image_instance.convert.return_value = mock_image_instance

        mock_draw = MagicMock()
        mock_image_draw.Draw.return_value = mock_draw

        # Создание объекта и вызов метода
        highlighter = ImageHighlighter(self.test_image_path)
        points = [(100, 200), (300, 400), (500, 600)]
        highlighter.highlight_points(points, radius=10, color="red")

        # Проверка вызова метода для каждой точки
        assert mock_draw.ellipse.call_count == 3
        mock_draw.ellipse.assert_any_call([90, 190, 110, 210], outline="red", width=2)
        mock_draw.ellipse.assert_any_call([290, 390, 310, 410], outline="red", width=2)
        mock_draw.ellipse.assert_any_call([490, 590, 510, 610], outline="red", width=2)

    @patch("src.infrastructure.utils.image_highlighter.Image")
    @patch("src.infrastructure.utils.image_highlighter.ImageDraw")
    def test_highlight_with_custom_params(self, mock_image_draw, mock_image):
        """Тест выделения точек с нестандартными параметрами"""
        # Настройка моков
        mock_image_instance = MagicMock()
        mock_image.open.return_value = mock_image_instance
        mock_image_instance.convert.return_value = mock_image_instance

        mock_draw = MagicMock()
        mock_image_draw.Draw.return_value = mock_draw

        # Создание объекта и вызов метода с нестандартными параметрами
        highlighter = ImageHighlighter(self.test_image_path)
        highlighter.highlight_points([(100, 200)], radius=20, color="yellow")

        # Проверка вызова метода с правильными параметрами
        mock_draw.ellipse.assert_called_once_with([80, 180, 120, 220], outline="yellow", width=2)

    @patch("src.infrastructure.utils.image_highlighter.Image")
    @patch("src.infrastructure.utils.image_highlighter.ImageDraw")
    def test_save_image(self, mock_image_draw, mock_image):
        """Тест сохранения обработанного изображения"""
        # Настройка моков
        mock_image_instance = MagicMock()
        mock_image.open.return_value = mock_image_instance
        mock_image_instance.convert.return_value = mock_image_instance

        mock_draw = MagicMock()
        mock_image_draw.Draw.return_value = mock_draw

        # Создание объекта и вызов метода сохранения
        highlighter = ImageHighlighter(self.test_image_path)
        highlighter.save(self.test_output_path)

        # Проверка вызова метода сохранения
        mock_image_instance.save.assert_called_once_with(self.test_output_path)

    @patch("src.infrastructure.utils.image_highlighter.Image")
    def test_image_open_error(self, mock_image):
        """Тест обработки ошибки при открытии изображения"""
        # Настройка мока для имитации исключения
        mock_image.open.side_effect = Exception("Cannot open image file")

        # Проверка вызова исключения
        with pytest.raises(Exception) as excinfo:
            highlighter = ImageHighlighter("nonexistent.jpg")

        assert "Cannot open image file" in str(excinfo.value)