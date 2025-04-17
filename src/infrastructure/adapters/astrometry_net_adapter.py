import time
import requests
import json
import os

from src.domain.interfaces.astrometry_service import IAstrometryService
from src.infrastructure.utils.logger import Logger


class AstrometryNetAdapter(IAstrometryService):
    BASE_URL = "http://nova.astrometry.net/api"

    def __init__(self, api_key):
        self.service_name = "AstrometryNetAdapter"
        self.api_key = api_key
        self.session = None
        self.logger = Logger()
        self.logger.info(self.service_name,"AstrometryAPIClient initialized")

    def login(self):
        url = f"{self.BASE_URL}/login"
        payload = {'request-json': json.dumps({"apikey": self.api_key})}

        self.logger.info(self.service_name,"Logging in to Astrometry.net API")
        self.logger.debug(self.service_name,f"Login URL: {url}")

        try:
            response = requests.post(url, data=payload)
            self.logger.debug(self.service_name,f"Response status: {response.status_code}")
            self.logger.debug(self.service_name,f"Response text: {response.text}")
            result = response.json()

            if result.get("status") != "success":
                self.logger.error(self.service_name,f"Login failed: {result}")
                raise Exception("Login failed")

            self.session = result["session"]
            self.logger.info(self.service_name,"Login successful")
            return result

        except Exception as e:
            self.logger.error(self.service_name,f"Login error: {str(e)}")
            raise

    def upload_image(self, image_path):
        if not self.session:
            self.login()

        url = f"{self.BASE_URL}/upload"
        self.logger.info(self.service_name,f"Uploading image: {image_path}")

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

                self.logger.debug(self.service_name,f"Upload URL: {url}")
                self.logger.debug(self.service_name,f"Upload payload: {request_json}")

                response = requests.post(url, data=data, files=files)
                self.logger.debug(self.service_name,f"Upload response status: {response.status_code}")
                self.logger.debug(self.service_name,f"Upload response text: {response.text}")

                try:
                    result = response.json()
                except json.JSONDecodeError:
                    self.logger.error(self.service_name,"JSON decode error from /upload. Server returned non-JSON.")
                    raise Exception("Error parsing JSON from /upload. Server returned non-JSON.")

                if result.get("status") != "success":
                    self.logger.error(self.service_name,f"Upload failed: {result}")
                    raise Exception(f"Upload failed: {result}")

                self.logger.info(self.service_name,f"Upload successful, submission ID: {result['subid']}")
                return result["subid"]
        except Exception as e:
            self.logger.error(self.service_name,f"Upload error: {str(e)}")
            raise

    def get_job_id(self, submission_id, timeout=300, interval=5):
        url = f"{self.BASE_URL}/submissions/{submission_id}"
        start_time = time.time()
        self.logger.info(self.service_name, f"Ожидание job_id для submission {submission_id}")

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                result = response.json()
                self.logger.debug(self.service_name, f"Статус submission: {result}")

                if result.get("processing_started"):
                    jobs = result.get("jobs", [])
                    if jobs:
                        job_id = jobs[0]
                        self.logger.info(self.service_name, f"Получен job_id: {job_id}")
                        return job_id

                self.logger.debug(self.service_name, f"Продолжаем ожидание job_id...")
                time.sleep(interval)

            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка проверки статуса submission: {str(e)}")
                time.sleep(interval)

        self.logger.error(self.service_name, f"Превышено время ожидания job_id ({timeout} сек)")
        return None

    def get_job_status(self, job_id):
        url = f"{self.BASE_URL}/jobs/{job_id}"
        self.logger.debug(self.service_name,f"Getting job status for job ID {job_id}")

        try:
            response = requests.get(url)
            result = response.json()
            self.logger.debug(self.service_name,f"Job status: {result}")
            return result
        except Exception as e:
            self.logger.error(self.service_name,f"Error getting job status: {str(e)}")
            raise

    def wait_for_job_completion(self, submission_id, timeout=600, interval=10):
        elapsed_time = 0
        self.logger.info(self.service_name, f"Ожидание завершения задания, submission ID: {submission_id}")

        while elapsed_time < timeout:
            try:
                url = f"{self.BASE_URL}/submissions/{submission_id}"
                response = requests.get(url, timeout=20)

                if response.status_code == 200:
                    status = response.json()
                    jobs = status.get('jobs', [])

                    if jobs:
                        for job_id in jobs:
                            try:
                                job_status = self.get_job_status(job_id)
                                if job_status.get('status') == 'success':
                                    self.logger.info(self.service_name, f"Задача {job_id} успешно завершена")
                                    return job_id
                            except Exception as e:
                                self.logger.error(self.service_name,
                                                  f"Ошибка проверки статуса задачи {job_id}: {str(e)}")

                self.logger.debug(self.service_name,
                                  f"Успешных задач пока нет, ожидание {interval} секунд. Прошло: {elapsed_time}с")

            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка при проверке статуса submission: {str(e)}")

            time.sleep(interval)
            elapsed_time += interval

        self.logger.warning(self.service_name, f"Превышено время ожидания {timeout} секунд")
        return None

    def calibrate_image(self, image_path):
        try:
            submission_id = self.upload_image(image_path)
            job_id = self.wait_for_job_completion(submission_id)

            if not job_id:
                self.logger.error(self.service_name,"The task did not complete successfully within the allotted time")
                return None

            self.logger.info(self.service_name,f"The task was completed successfully, the task ID {job_id}")

            base_dir = os.path.dirname(image_path)
            base_name = os.path.splitext(os.path.basename(image_path))[0]

            wcs_path = os.path.join(base_dir, f"{base_name}_wcs.fits")
            rdls_path = os.path.join(base_dir, f"{base_name}_rdls.rdls")

            self.download_result_file(job_id, "wcs_file", wcs_path)
            self.download_result_file(job_id, "rdls_file", rdls_path)

            return {
                "job_id": job_id,
                "wcs_path": wcs_path,
                "rdls_path": rdls_path
            }

        except Exception as e:
            self.logger.error(self.service_name,f"Error in the astrometric calibration process: {str(e)}")
            return None

    def download_result_file(self, job_id, file_type, save_path):
        url = f"http://nova.astrometry.net/{file_type}/{job_id}"
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp")
        os.makedirs(temp_dir, exist_ok=True)

        original_filename = os.path.basename(save_path)
        temp_save_path = os.path.join(temp_dir, original_filename)

        self.logger.info(self.service_name,f"Downloading {file_type} from {url}")
        self.logger.info(self.service_name,f"Original save path: {save_path}")
        self.logger.info(self.service_name,f"Temporary save path for debugging: {temp_save_path}")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(self.service_name,f"Successfully downloaded {file_type} to {save_path}")
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(self.service_name,f"Also saved to original location: {save_path}")
                return True
            else:
                self.logger.error(self.service_name,f"Failed to download {file_type}, status code: {response.status_code}")
                raise Exception(
                    f"Failed to upload {file_type} for job {job_id}, response code: {response.status_code}")
        except Exception as e:
            self.logger.error(self.service_name,f"Error downloading {file_type}: {str(e)}")
            raise