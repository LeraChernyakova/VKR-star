from domain.interfaces.astrometry_service import IAstrometryService


class AstrometryNetAdapter(IAstrometryService):
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = AstrometryAPIClient(api_key)

    def calibrate_image(self, image_path):
        # Реализация взаимодействия с Astrometry.net
        submission_id = self.client.upload_image(image_path)
        job_id = self._wait_for_job(submission_id)

        # Загрузка WCS файлов и т.д.
        # ...

        return wcs_data