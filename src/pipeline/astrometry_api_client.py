import requests
import json
from src.utils.logger import Logger


class AstrometryAPIClient:
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

    def get_submission_status(self, subid):
        url = f"{self.BASE_URL}/submissions/{subid}"
        self.logger.debug(f"Checking submission status for ID {subid}")

        try:
            response = requests.get(url)
            self.logger.debug(f"Submission status response code: {response.status_code}")
            self.logger.debug(f"Submission status response text: {response.text}")

            try:
                result = response.json()
                self.logger.debug(f"Submission status: {result}")
                return result
            except json.JSONDecodeError:
                self.logger.error("JSON decode error from /submissions")
                raise Exception("Error parsing JSON from /submissions")
        except Exception as e:
            self.logger.error(f"Error getting submission status: {str(e)}")
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

    def get_job_result(self, job_id):
        url = f"{self.BASE_URL}/jobs/{job_id}/calibration/"
        self.logger.info(f"Getting calibration results for job ID {job_id}")

        try:
            response = requests.get(url)
            result = response.json()
            self.logger.debug(f"Job result received: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error getting job result: {str(e)}")
            raise

    def get_annotations(self, job_id):
        url = f"{self.BASE_URL}/jobs/{job_id}/annotations/"
        self.logger.info(f"Getting annotations for job ID {job_id}")

        try:
            response = requests.get(url)
            result = response.json()
            self.logger.debug(f"Annotations received: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error getting annotations: {str(e)}")
            raise
