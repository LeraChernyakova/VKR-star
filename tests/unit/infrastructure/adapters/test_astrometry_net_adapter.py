import pytest
from unittest.mock import Mock, patch, mock_open
import json
import os
from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter


class TestAstrometryNetAdapter:
    def setup_method(self):
        self.api_key = "test_api_key"
        self.test_image_path = "test_image.jpg"
        self.adapter = AstrometryNetAdapter(self.api_key)

    @patch('requests.post')
    def test_login_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "session": "test_session"}
        mock_post.return_value = mock_response

        result = self.adapter.login()

        mock_post.assert_called_once()
        assert self.adapter.session == "test_session"
        assert result["status"] == "success"

    @patch('requests.post')
    def test_login_failure(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "error", "message": "Invalid API key"}
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            self.adapter.login()

        assert "Login failed" in str(exc_info.value)
        mock_post.assert_called_once()

    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.login')
    @patch('requests.post')
    def test_upload_image_success(self, mock_post, mock_login):
        self.adapter.session = "test_session"
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "subid": 12345}
        mock_post.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image_data")):
            result = self.adapter.upload_image(self.test_image_path)

        mock_post.assert_called_once()
        assert result == 12345
        mock_login.assert_not_called()

    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.login')
    @patch('requests.post')
    def test_upload_image_with_login(self, mock_post, mock_login):
        self.adapter.session = None
        mock_login.return_value = {"status": "success", "session": "test_session"}
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "subid": 12345}
        mock_post.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image_data")):
            result = self.adapter.upload_image(self.test_image_path)

        mock_login.assert_called_once()
        mock_post.assert_called_once()
        assert result == 12345

    @patch('requests.post')
    def test_upload_image_failure(self, mock_post):
        self.adapter.session = "test_session"
        mock_response = Mock()
        mock_response.json.return_value = {"status": "error", "message": "Upload failed"}
        mock_post.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image_data")):
            with pytest.raises(Exception) as exc_info:
                self.adapter.upload_image(self.test_image_path)

        assert "Upload failed" in str(exc_info.value)

    @patch('requests.get')
    def test_get_job_id_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "processing_started": True,
            "jobs": [12345]
        }
        mock_get.return_value = mock_response

        result = self.adapter.get_job_id(54321, timeout=1, interval=0.1)

        assert result == 12345
        mock_get.assert_called()

    @patch('requests.get')
    def test_get_job_id_timeout(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "processing_started": False,
            "jobs": []
        }
        mock_get.return_value = mock_response

        result = self.adapter.get_job_id(54321, timeout=0.2, interval=0.1)

        assert result is None
        mock_get.assert_called()

    @patch('requests.get')
    def test_get_job_status(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "job_id": 12345}
        mock_get.return_value = mock_response

        result = self.adapter.get_job_status(12345)

        assert result["status"] == "success"
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_wait_for_job_completion_success(self, mock_get):
        mock_submission_response = Mock()
        mock_submission_response.status_code = 200
        mock_submission_response.json.return_value = {"jobs": [12345]}

        mock_job_status_response = Mock()
        mock_job_status_response.json.return_value = {"status": "success"}

        mock_get.side_effect = [mock_submission_response, mock_job_status_response]

        result = self.adapter.wait_for_job_completion(54321, timeout=1, interval=0.1)

        assert result == 12345
        assert mock_get.call_count == 2

    @patch('requests.get')
    def test_wait_for_job_completion_timeout(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": []}
        mock_get.return_value = mock_response

        # Выполнение с коротким таймаутом
        result = self.adapter.wait_for_job_completion(54321, timeout=0.2, interval=0.1)

        # Проверки
        assert result is None
        mock_get.assert_called()

    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.upload_image')
    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.wait_for_job_completion')
    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.download_result_file')
    def test_calibrate_image_success(self, mock_download, mock_wait, mock_upload):
        mock_upload.return_value = 54321
        mock_wait.return_value = 12345
        mock_download.return_value = True

        result = self.adapter.calibrate_image(self.test_image_path)

        assert result["job_id"] == 12345
        assert "wcs_path" in result
        assert "rdls_path" in result
        mock_upload.assert_called_once_with(self.test_image_path)
        mock_wait.assert_called_once_with(54321)
        assert mock_download.call_count == 2

    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.upload_image')
    @patch('src.infrastructure.adapters.astrometry_net_adapter.AstrometryNetAdapter.wait_for_job_completion')
    def test_calibrate_image_no_job_id(self, mock_wait, mock_upload):
        mock_upload.return_value = 54321
        mock_wait.return_value = None

        result = self.adapter.calibrate_image(self.test_image_path)

        assert result is None
        mock_upload.assert_called_once()
        mock_wait.assert_called_once()

    @patch('requests.get')
    def test_download_result_file_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"file_content"
        mock_get.return_value = mock_response

        with patch("builtins.open", mock_open()) as mock_file:
            self.adapter.download_result_file(12345, "wcs_file", "output.fits")

        mock_get.assert_called_once()
        mock_file.assert_called()
        mock_file().write.assert_called_with(b"file_content")

    @patch('requests.get')
    def test_download_result_file_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404  # Ошибка
        mock_get.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            self.adapter.download_result_file(12345, "wcs_file", "output.fits")

        assert "Failed to upload" in str(exc_info.value)
        mock_get.assert_called_once()