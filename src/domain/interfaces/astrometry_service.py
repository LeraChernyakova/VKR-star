from abc import ABC, abstractmethod


class IAstrometryService(ABC):
    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def upload_image(self, image_path):
        pass

    @abstractmethod
    def get_job_status(self, job_id):
        pass

    @abstractmethod
    def download_result_file(self, job_id, file_type, save_path):
        pass
