import os

from astrometry_net_client import Client as AstrometryNetClient
from astropy.wcs import WCS

from src.domain.interfaces.astrometry_service import IAstrometryService
from src.infrastructure.utils.image_highlighter import ImageHighlighter
from src.infrastructure.utils.logger import Logger


class AstrometryNetAdapter(IAstrometryService):
    def __init__(self, api_key):
        self.service_name = "AstrometryNetAdapter"
        self.api_key = api_key
        self.session = None
        self.logger = Logger()
        try:
            self.client = AstrometryNetClient(api_key=api_key)
        except Exception as e:
            self.logger.error(self.service_name, f"Client init failed: {e}")
            raise

    def calibrate_image(self, image_path: str, timeout: int = 600):
        try:
            job = self.client.upload_file(image_path)
            job.until_done()
            job_id = getattr(job, "id", None)
            if not job_id or not job.success():
                self.logger.error(self.service_name, "Калибровка не удалась")
                return None

            rdls_hdul = job.rdls_file()
            data = rdls_hdul[1].data

            known_mask = data['ref_id'] != -1
            ra_known = data['RA'][known_mask]
            dec_known = data['DEC'][known_mask]

            wcs_header = job.wcs_file()
            wcs = WCS(wcs_header)
            x_pix, y_pix = wcs.all_world2pix(ra_known, dec_known, 0)
            pixel_coords = list(zip(x_pix, y_pix))

            output_dir = r"F:\ETU\VKR\repo\VKR-star\temp"
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_known_highlighted.png")
            highlighter = ImageHighlighter(image_path)
            highlighter.highlight_points(pixel_coords, radius=10, color="green")
            highlighter.save(output_path)

            return {
                "pixel_coords": pixel_coords
            }
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка калибровки: {e}")
            return None