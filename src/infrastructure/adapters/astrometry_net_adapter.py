import os

from astropy.wcs import WCS
from src.infrastructure.utils.logger import Logger
from astrometry_net_client import Client as AstrometryNetClient
from src.domain.interfaces.astrometry_service import IAstrometryService
from src.infrastructure.utils.image_highlighter import ImageHighlighter


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
                self.logger.error(self.service_name, "Calibration failed")
                return None

            rdls_hdul = job.rdls_file()
            data = rdls_hdul[1].data
            if 'ref_id' in data.names:
                known_mask = data['ref_id'] != -1
                ra_known = data['RA'][known_mask]
                dec_known = data['DEC'][known_mask]
            else:
                ra_known = data['RA']
                dec_known = data['DEC']

            wcs_header = job.wcs_file()
            wcs = WCS(wcs_header, relax=True)
            x_pix, y_pix = wcs.all_world2pix(ra_known, dec_known, 0)
            pixel_coords = list(zip(x_pix, y_pix))

            pixel_xy = [(x, y) for (x, y) in pixel_coords]
            highlighter = ImageHighlighter(image_path)
            highlighter.highlight_points(pixel_xy, radius=8, color="green")
            base, ext = os.path.splitext(image_path)
            base = base.replace("test-image", "processing")
            os.makedirs(os.path.dirname(base), exist_ok=True)
            filtered_vis_path = f"{base}_astrometry{ext}"
            print(filtered_vis_path)
            highlighter.save(filtered_vis_path)

            return {
                "pixel_coords": pixel_coords,
                "wcs": wcs
            }

        except Exception as e:
            self.logger.error(self.service_name, f"Calibration error: {e}")
            return None