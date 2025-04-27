import pytest
from unittest.mock import Mock, patch
import os
from src.infrastructure.service.file_dialog_service import FileDialogService


class TestFileDialogService:
    def setup_method(self):
        """Настройка среды для каждого теста"""
        self.service = FileDialogService()

    def test_initialization(self):
        """Тест инициализации сервиса"""
        assert self.service.service_name == "FileDialogService"
        assert hasattr(self.service, "logger")

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("os.path.isfile")
    def test_select_image_success(self, mock_isfile, mock_askopenfilename, mock_tk):
        """Тест успешного выбора изображения"""
        # Настройка моков
        mock_askopenfilename.return_value = "/path/to/image.jpg"
        mock_isfile.return_value = True

        # Вызов метода
        result = self.service.select_image()

        # Проверки
        assert result == "/path/to/image.jpg"
        mock_askopenfilename.assert_called_once()
        mock_isfile.assert_called_once_with("/path/to/image.jpg")

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    def test_select_image_cancel(self, mock_askopenfilename, mock_tk):
        """Тест отмены выбора изображения"""
        # Настройка моков
        mock_askopenfilename.return_value = ""

        # Вызов метода
        result = self.service.select_image()

        # Проверки
        assert result is None
        mock_askopenfilename.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("os.path.isfile")
    def test_select_nonexistent_file(self, mock_isfile, mock_askopenfilename, mock_tk):
        """Тест выбора несуществующего файла"""
        # Настройка моков
        mock_askopenfilename.return_value = "/path/to/nonexistent.jpg"
        mock_isfile.return_value = False

        # Вызов метода
        result = self.service.select_image()

        # Проверки
        assert result is None
        mock_askopenfilename.assert_called_once()
        mock_isfile.assert_called_once_with("/path/to/nonexistent.jpg")