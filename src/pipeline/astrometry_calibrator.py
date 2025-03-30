import os
import time
from src.pipeline.processing_chain import ProcessingChain
from src.pipeline.astrometry_api_client import AstrometryAPIClient
from src.utils.logger import Logger


class AstrometryCalibrator(ProcessingChain):
    def __init__(self, api_key, next_processor=None):
        super().__init__(next_processor)
        self.client = AstrometryAPIClient(api_key)
        self.logger = Logger()

    def handle(self, image_path):
        try:
            self.logger.info(f"Starting astrometric calibration for image: {image_path}")
            submission_id = self.client.upload_image(image_path)
            self.logger.info(f"Image uploaded, submission ID: {submission_id}")

            job_id = self.wait_for_job_completion(submission_id)
            if job_id:
                self.logger.info(f"Job completed successfully, job ID: {job_id}")
                base_dir = os.path.dirname(image_path)
                base_name = os.path.splitext(os.path.basename(image_path))[0]

                wcs_path = os.path.join(base_dir, f"{base_name}_wcs.fits")
                rdls_path = os.path.join(base_dir, f"{base_name}_rdls.rdls")

                self.client.download_result_file(job_id, "wcs_file", wcs_path)
                self.client.download_result_file(job_id, "rdls_file", rdls_path)

                context = {
                    "image_path": image_path,
                    "job_id": job_id,
                    "wcs_path": wcs_path,
                    "rdls_path": rdls_path
                }

                if self.next_processor:
                    return self.next_processor.handle(context)

                return context
            else:
                self.logger.error('Job did not complete successfully within the timeout period')
                raise Exception('Job did not complete successfully')
        except Exception as e:
            self.logger.error(f'Error during astrometric calibration: {e}')
            return None

    def wait_for_job_completion(self, submission_id, timeout=300, interval=5):
        elapsed_time = 0
        self.logger.info(f"Waiting for job completion, submission ID: {submission_id}")

        while elapsed_time < timeout:
            status = self.client.get_submission_status(submission_id)
            jobs = status.get('jobs', [])
            if jobs:
                for job_id in jobs:
                    self.logger.debug(f"Checking job status for job ID: {job_id}")
                    job_status = self.client.get_job_status(job_id)
                    if job_status.get('status') == 'success':
                        self.logger.info(f"Job {job_id} completed successfully")
                        return job_id
            self.logger.debug(f"No successful jobs yet, waiting {interval} seconds. Elapsed: {elapsed_time}s")
            time.sleep(interval)
            elapsed_time += interval

        self.logger.warning(f"Timeout after {timeout} seconds waiting for job completion")
        return None

