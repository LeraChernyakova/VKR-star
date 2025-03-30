from src.pipeline.processing_chain import ProcessingChain
from src.utils.image_highlighter import ImageHighlighter
from src.pipeline.celestial_catalog_adapter import CelestialCatalogAdapter
from src.utils.logger import Logger

from astropy.io import fits, ascii
from astropy.wcs import WCS

import os
from astropy.time import Time
import datetime


class ObjectClassifier(ProcessingChain):
    def __init__(self, next_processor=None):
        super().__init__(next_processor)
        self.catalog = CelestialCatalogAdapter()
        self.logger = Logger()
        self.logger.info("ObjectClassifier initialized")

    def handle(self, context: dict):
        if not context:
            self.logger.error("Empty context received")
            return context

        try:
            self.logger.info("Starting object classification")

            if "wcs_path" not in context or "rdls_path" not in context:
                self.logger.error("Missing required files in context: wcs_path or rdls_path")
                return context

            self.logger.debug(f"Loading WCS data from {context['wcs_path']}")
            try:
                wcs = WCS(fits.open(context["wcs_path"], ignore_missing_simple=True)[0].header)
            except Exception as e:
                self.logger.error(f"Failed to load WCS file: {e}")
                return context

            unknown_points = []
            known_points = []

            try:
                self.logger.debug(f"Loading RDLS data from {context['rdls_path']}")
                # Try with format='csv' and guess=False options to handle binary data
                rdls = ascii.read(context["rdls_path"], format='csv', guess=False, encoding='latin1')
                self.logger.info(f"Found {len(rdls)} detected objects in RDLS file")

                # ASCII format typically has 'X' and 'Y' columns
                x_column, y_column = 'X', 'Y'

            except Exception as e1:
                self.logger.warning(f"First attempt to read RDLS failed: {e1}")
                try:
                    # Alternative method using a different format or reader
                    rdls = fits.open(context["rdls_path"], ignore_missing_simple=True)[1].data
                    self.logger.info(f"Found {len(rdls)} detected objects in RDLS file using FITS reader")

                    # Check for column names in FITS format
                    column_names = rdls.names if hasattr(rdls, 'names') else []
                    self.logger.debug(f"Available columns in RDLS file: {column_names}")

                    # Determine appropriate column names for coordinates
                    if 'x' in column_names:
                        x_column, y_column = 'x', 'y'
                    elif 'X' in column_names:
                        x_column, y_column = 'X', 'Y'
                    elif 'FIELD_X' in column_names:
                        x_column, y_column = 'FIELD_X', 'FIELD_Y'
                    else:
                        # If we can't determine the column names, log and return
                        self.logger.error(
                            f"Could not find coordinate columns in RDLS data. Available columns: {column_names}")
                        return context
                except Exception as e2:
                    self.logger.error(f"Failed to load RDLS file with all methods: {e2}")
                    return context

            # Process all objects in the RDLS file
            for i, row in enumerate(rdls):
                try:
                    x, y = row[x_column], row[y_column]
                    ra, dec = wcs.all_pix2world([[x, y]], 1)[0]

                    self.logger.debug(f"Object {i + 1}: (x,y)=({x:.1f},{y:.1f}) -> (RA,Dec)=({ra:.6f}°,{dec:.6f}°)")
                    results = self.catalog.query_all(ra, dec, radius_arcsec=3)

                    if not results:
                        self.logger.info(f"Object {i + 1} at (RA,Dec)=({ra:.6f}°,{dec:.6f}°) classified as UNKNOWN")
                        unknown_points.append((x, y))
                    else:
                        self.logger.debug(f"Object {i + 1} at (RA,Dec)=({ra:.6f}°,{dec:.6f}°) classified as KNOWN")
                        known_points.append((x, y))
                except Exception as e:
                    self.logger.warning(f"Error processing object {i + 1}: {e}")
                    continue

            self.logger.info(
                f"Classification complete: {len(known_points)} known objects, {len(unknown_points)} unknown objects")

            if "image_path" in context and os.path.exists(context["image_path"]):
                self.logger.info(f"Highlighting unknown objects on image {context['image_path']}")
                highlighter = ImageHighlighter(context["image_path"])
                highlighter.highlight_points(unknown_points, radius=12, color="red")

                output_path = os.path.splitext(context["image_path"])[0] + "_highlighted.jpg"
                highlighter.save(output_path)
                self.logger.info(f"Saved highlighted image to {output_path}")

                context["highlighted_path"] = output_path
            else:
                self.logger.warning("Image path missing or invalid, skipping highlighting")

            context["unknown_objects"] = unknown_points
            context["known_objects"] = known_points
            context["unknown_count"] = len(unknown_points)
            context["total_objects"] = len(rdls)

            self.logger.info("ObjectClassifier processing complete")
            return context

        except Exception as e:
            self.logger.error(f"Error during object classification: {e}")
            return context
