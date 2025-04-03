import os
import numpy as np
from PIL import Image
import sep

from src.utils.image_highlighter import ImageHighlighter
from src.utils.logger import Logger
from src.pipeline.processing_chain import ProcessingChain


class SExtractorProcessor(ProcessingChain):
    def __init__(self, next_processor=None):
        super().__init__(next_processor)
        self.logger = Logger()
        self.logger.info("SExtractorProcessor initialized")

    def handle(self, context):
        if not context or "image_path" not in context:
            self.logger.error("No image path in context")
            return context

        try:
            image_path = context["image_path"]
            self.logger.info(f"Processing image with SEP: {image_path}")

            # Load the image
            image = Image.open(image_path).convert("L")
            data = np.array(image, dtype=np.float32)

            # Remove background
            bkg = sep.Background(data)
            data_sub = data - bkg

            # Higher threshold (5.0 instead of 3.5) for more reliable detections
            # Increased minarea to filter out smaller noise artifacts
            objects = sep.extract(data_sub, thresh=5.0, err=bkg.globalrms,
                                  deblend_nthresh=32, deblend_cont=0.005,
                                  minarea=10, filter_kernel=None)

            # Calculate flux for each object
            flux, flux_err, flag = sep.sum_circle(data_sub, objects['x'], objects['y'],
                                                  r=5.0, err=bkg.globalrms)

            # Filter objects by minimum flux to eliminate noise
            min_flux = np.median(flux) * 0.3  # Adjust this threshold as needed
            bright_objects_mask = flux > min_flux
            bright_objects = objects[bright_objects_mask]
            bright_flux = flux[bright_objects_mask]

            self.logger.info(f"Found {len(objects)} initial objects, kept {len(bright_objects)} after flux filtering")

            # Store results in context
            context["sep_objects"] = bright_objects
            context["sep_pixel_coords"] = [(obj['x'], obj['y']) for obj in bright_objects]
            context["sep_flux"] = bright_flux

            # Create visualization
            if "image_path" in context:
                self.logger.info(f"Creating image with all SExtractor detections")
                sep_highlighter = ImageHighlighter(context["image_path"])
                sep_highlighter.highlight_points(context["sep_pixel_coords"], radius=12, color="purple")

                sep_output_path = os.path.splitext(context["image_path"])[0] + "_sep_all_objects.jpg"
                sep_highlighter.save(sep_output_path)
                context["sep_all_objects_path"] = sep_output_path

            return context
        except Exception as e:
            self.logger.error(f"Error in SExtractor processing: {str(e)}")
            return context