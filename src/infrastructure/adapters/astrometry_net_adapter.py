import requests
import json
import os

from src.domain.interfaces.astrometry_service import IAstrometryService
from src.infrastructure.utils.logger import Logger


class AstrometryNetAdapter(IAstrometryService):
    BASE_URL = "http://nova.astrometry.net/api"

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = None
        self.logger = Logger()
        self.logger.info("AstrometryAPIClient initialized")

    def login(self):
        url = f"{self.BASE_URL}/login"
        payload = {'request-json': json.dumps({"apikey": self.api_key})}

        self.logger.info("Logging in to Astrometry.net API")
        self.logger.debug(f"Login URL: {url}")

        try:
            response = requests.post(url, data=payload)
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response text: {response.text}")
            result = response.json()

            if result.get("status") != "success":
                self.logger.error(f"Login failed: {result}")
                raise Exception("Login failed")

            self.session = result["session"]
            self.logger.info("Login successful")
            return result

        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            raise

    def upload_image(self, image_path):
        if not self.session:
            self.login()

        url = f"{self.BASE_URL}/upload"
        self.logger.info(f"Uploading image: {image_path}")

        try:
            with open(image_path, 'rb') as f:
                files = {
                    'file': (image_path, f, 'application/octet-stream')
                }
                request_json = {
                    "publicly_visible": "y",
                    "allow_modifications": "d",
                    "allow_commercial_use": "d",
                    "session": self.session
                }
                data = {
                    'request-json': json.dumps(request_json)
                }

                self.logger.debug(f"Upload URL: {url}")
                self.logger.debug(f"Upload payload: {request_json}")

                response = requests.post(url, data=data, files=files)
                self.logger.debug(f"Upload response status: {response.status_code}")
                self.logger.debug(f"Upload response text: {response.text}")

                try:
                    result = response.json()
                except json.JSONDecodeError:
                    self.logger.error("JSON decode error from /upload. Server returned non-JSON.")
                    raise Exception("Error parsing JSON from /upload. Server returned non-JSON.")

                if result.get("status") != "success":
                    self.logger.error(f"Upload failed: {result}")
                    raise Exception(f"Upload failed: {result}")

                self.logger.info(f"Upload successful, submission ID: {result['subid']}")
                return result["subid"]
        except Exception as e:
            self.logger.error(f"Upload error: {str(e)}")
            raise

    def get_job_status(self, job_id):
        url = f"{self.BASE_URL}/jobs/{job_id}"
        self.logger.debug(f"Getting job status for job ID {job_id}")

        try:
            response = requests.get(url)
            result = response.json()
            self.logger.debug(f"Job status: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error getting job status: {str(e)}")
            raise

    def download_result_file(self, job_id, file_type, save_path):
        url = f"http://nova.astrometry.net/{file_type}/{job_id}"
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp")
        os.makedirs(temp_dir, exist_ok=True)

        original_filename = os.path.basename(save_path)
        temp_save_path = os.path.join(temp_dir, original_filename)

        self.logger.info(f"Downloading {file_type} from {url}")
        self.logger.info(f"Original save path: {save_path}")
        self.logger.info(f"Temporary save path for debugging: {temp_save_path}")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Successfully downloaded {file_type} to {save_path}")
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Also saved to original location: {save_path}")
                return True
            else:
                self.logger.error(f"Failed to download {file_type}, status code: {response.status_code}")
                raise Exception(
                    f"Не удалось загрузить {file_type} для job {job_id}, код ответа: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error downloading {file_type}: {str(e)}")
            raise