import numpy as np
import sep
import os

from PIL import Image
from src.domain.interfaces.object_detection_service import IObjectDetectionService
from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter


class SepDetectionAdapter(IObjectDetectionService):
    def __init__(self):
        self.service_name = "SepDetectionAdapter"
        self.logger = Logger()
        self.logger.info(self.service_name,"SepDetectionAdapter initialized")

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

            output_dir = r"F:\ETU\VKR\repo\VKR-star\temp"
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_sep_highlighted.png")
            pixel_coords = [(obj['x'], obj['y']) for obj in bright_objects]
            highlighter = ImageHighlighter(image_path)
            highlighter.highlight_points(pixel_coords, radius=10, color="red")
            highlighter.save(output_path)
            self.logger.info(self.service_name, f"Сохранено изображение с SEP-объектами: {output_path}")

            return {
                "objects": bright_objects,
                "pixel_coords": [(obj['x'], obj['y']) for obj in bright_objects],
                "flux": bright_flux
            }

        except Exception as e:
            self.logger.error(self.service_name,f"Error in SEP processing: {str(e)}")
            return {"error": str(e)}