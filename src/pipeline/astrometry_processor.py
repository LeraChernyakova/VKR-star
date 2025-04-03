import os
from src.pipeline.processing_chain import ProcessingChain
from src.pipeline.astrometry_api_client import AstrometryAPIClient
from src.utils.logger import Logger

class AstrometryProcessor(ProcessingChain):
    def __init__(self, api_key, next_processor=None):
        super().__init__(next_processor)
        self.client = AstrometryAPIClient(api_key)
        self.logger = Logger()
        self.logger.info("AstrometryProcessor initialized")

    def handle(self, context):
        if not context or "image_path" not in context:
            self.logger.error("No image path in context")
            return context

        try:
            image_path = context["image_path"]
            self.logger.info(f"Processing image with Astrometry.net: {image_path}")

            submission_id = self.client.upload_image(image_path)
            job_id = self._wait_for_job(submission_id)
            if not job_id:
                return context

            base_dir = os.path.dirname(image_path)
            base_name = os.path.splitext(os.path.basename(image_path))[0]

            wcs_path = os.path.join(base_dir, f"{base_name}_wcs.fits")
            rdls_path = os.path.join(base_dir, f"{base_name}_rdls.rdls")

            self.client.download_result_file(job_id, "wcs_file", wcs_path)
            self.client.download_result_file(job_id, "rdls_file", rdls_path)

            context["job_id"] = job_id
            context["wcs_path"] = wcs_path
            context["rdls_path"] = rdls_path

            from src.pipeline.object_classifier import ObjectClassifier
            object_classifier = ObjectClassifier()
            object_classifier.handle(context)

            return context
        except Exception as e:
            self.logger.error(f"Error in Astrometry.net processing: {str(e)}")
            return context

    def _wait_for_job(self, subid, timeout=300, interval=5):
        import time
        elapsed = 0
        while elapsed < timeout:
            status = self.client.get_submission_status(subid)
            jobs = status.get("jobs", [])
            for job_id in jobs:
                if job_id:
                    job_status = self.client.get_job_status(job_id)
                    if job_status.get("status") == "success":
                        return job_id
                    elif job_status.get("status") == "failure":
                        raise Exception("Astrometry processing failed")
            time.sleep(interval)
            elapsed += interval
        return None