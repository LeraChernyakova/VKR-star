import os
import numpy as np
from src.pipeline.processing_chain import ProcessingChain
from src.infrastructure.utils.image_highlighter import ImageHighlighter
from src.infrastructure.utils.logger import Logger

class ComparisonProcessor(ProcessingChain):
    def __init__(self, next_processor=None):
        super().__init__(next_processor)
        self.logger = Logger()
        self.logger.info("ComparisonProcessor initialized")

    def handle(self, context):
        if "sep_pixel_coords" not in context:
            self.logger.warning("Missing SExtractor pixel coordinates, skipping comparison")
            context["unique_sep_objects"] = []  # Initialize with empty list
            return context

        if "all_objects" not in context:
            self.logger.warning("Missing Astrometry.net objects, treating all SExtractor objects as unique")
            # If no astrometry objects, all SExtractor objects are "unique"
            context["unique_sep_objects"] = context["sep_pixel_coords"]
            if "image_path" in context and context["sep_pixel_coords"]:
                self._create_unique_objects_visualization(context)
            return context

            # Original comparison logic continues here...
        sep_coords = np.array(context["sep_pixel_coords"])
        astrometry_coords = np.array(context["all_objects"])

        unique_objects = []
        match_threshold = 10

        for sep_x, sep_y in sep_coords:
            if len(astrometry_coords) > 0:
                distances = np.sqrt((astrometry_coords[:, 0] - sep_x)**2 +
                                  (astrometry_coords[:, 1] - sep_y)**2)
                if np.min(distances) > match_threshold:
                    unique_objects.append((sep_x, sep_y))
            else:
                unique_objects.append((sep_x, sep_y))

        context["unique_sep_objects"] = unique_objects
        self.logger.info(f"Found {len(unique_objects)} objects unique to SExtractor")

        if unique_objects and "image_path" in context:
            highlighter = ImageHighlighter(context["image_path"])
            highlighter.highlight_points(unique_objects, radius=12, color="green")

            output_path = os.path.splitext(context["image_path"])[0] + "_unique_objects.jpg"
            highlighter.save(output_path)
            context["unique_objects_path"] = output_path

        return context