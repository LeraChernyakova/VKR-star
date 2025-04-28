import numpy as np
import sep

from PIL import Image
from src.domain.interfaces.object_detection_service import IObjectDetectionService
from src.infrastructure.utils.logger import Logger


class SepDetectionAdapter(IObjectDetectionService):
    def __init__(self):
        self.service_name = "SepDetectionAdapter"
        self.logger = Logger()

    def detect_objects(self, image_path, wcs_path=None):
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

            return {
                "pixel_coords": [
                    {
                        "x": obj['x'],
                        "y": obj['y'],
                        "flux": float(f),
                        "a": float(obj['a']),
                        "b": float(obj['b']),
                        "theta": float(obj['theta']),
                        "npix": int(obj['npix']),
                        "flag": int(obj['flag'])
                    }
                    for obj, f in zip(bright_objects, flux[bright_objects_mask])
                ]
            }
        except Exception as e:
            self.logger.error(self.service_name,f"Error in SEP processing: {str(e)}")
            return {"error": str(e)}