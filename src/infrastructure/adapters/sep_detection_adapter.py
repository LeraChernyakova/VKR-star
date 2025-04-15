import numpy as np
import sep
from PIL import Image
from src.domain.interfaces.object_detection_service import IObjectDetectionService
from src.infrastructure.utils.logger import Logger


class SepDetectionAdapter(IObjectDetectionService):
    def __init__(self):
        self.logger = Logger()
        self.logger.info("SepDetectionAdapter initialized")

    def detect_objects(self, image_path):
        try:
            image = Image.open(image_path).convert("L")
            data = np.array(image, dtype=np.float32)

            bkg = sep.Background(data)
            data_sub = data - bkg

            objects = sep.extract(data_sub, thresh=5.0, err=bkg.globalrms,
                                  deblend_nthresh=32, deblend_cont=0.005,
                                  minarea=10, filter_kernel=None)

            flux, flux_err, flag = sep.sum_circle(data_sub, objects['x'], objects['y'],
                                                  r=5.0, err=bkg.globalrms)

            min_flux = np.median(flux) * 0.3
            bright_objects_mask = flux > min_flux
            bright_objects = objects[bright_objects_mask]
            bright_flux = flux[bright_objects_mask]

            self.logger.info(f"Found {len(objects)} initial objects, kept {len(bright_objects)} after flux filtering")

            return {
                "objects": bright_objects,
                "pixel_coords": [(obj['x'], obj['y']) for obj in bright_objects],
                "flux": bright_flux
            }

        except Exception as e:
            self.logger.error(f"Error in SEP processing: {str(e)}")
            return {"error": str(e)}