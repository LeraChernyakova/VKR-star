import pytest
from unittest.mock import Mock
from src.application.use_cases.select_image_use_case import SelectImageUseCase


class TestSelectImageUseCase:
    def setup_method(self):
        self.mock_file_service = Mock()
        self.use_case = SelectImageUseCase(self.mock_file_service)

    def test_execute_returns_selected_path(self):
        expected_path = "/path/to/image.jpg"
        self.mock_file_service.select_image.return_value = expected_path

        result = self.use_case.execute()

        self.mock_file_service.select_image.assert_called_once()
        assert result == expected_path

    def test_execute_returns_none_when_no_selection(self):
        self.mock_file_service.select_image.return_value = None

        result = self.use_case.execute()

        self.mock_file_service.select_image.assert_called_once()
        assert result is None