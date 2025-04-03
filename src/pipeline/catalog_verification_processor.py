import os
import numpy as np
from astropy.wcs import WCS
import warnings
from astropy.wcs import FITSFixedWarning
from astropy.io import fits

from src.pipeline.processing_chain import ProcessingChain
from src.pipeline.celestial_catalog_adapter import CelestialCatalogAdapter
from src.utils.image_highlighter import ImageHighlighter
from src.utils.logger import Logger


class CatalogVerificationProcessor(ProcessingChain):
    def __init__(self, next_processor=None):
        super().__init__(next_processor)
        self.catalog = CelestialCatalogAdapter()
        self.logger = Logger()
        self.logger.info("CatalogVerificationProcessor initialized")

    def handle(self, context):
        """Verify SExtractor-unique objects against astronomical catalogs"""
        if "unique_sep_objects" not in context:
            self.logger.warning("No unique SExtractor objects found, skipping catalog verification")
            context["truly_unknown_objects"] = []
            return context

        if "wcs_path" not in context:
            self.logger.warning("Missing WCS data, cannot perform catalog verification")
            # Without WCS we can't convert pixel to sky coordinates
            context["truly_unknown_objects"] = []
            return context

        try:
            # Load WCS data for coordinate conversion
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', FITSFixedWarning)
                with fits.open(context["wcs_path"], ignore_missing_simple=True) as hdul:
                    wcs = WCS(hdul[0].header)
                    header = hdul[0].header
                    field_ra = header.get('CRVAL1')
                    field_dec = header.get('CRVAL2')
                    context["field_center"] = {
                        "ra": field_ra,
                        "dec": field_dec,
                        "ra_formatted": self._format_ra(field_ra) if field_ra is not None else "Unknown",
                        "dec_formatted": self._format_dec(field_dec) if field_dec is not None else "Unknown"
                    }

            unique_objects = context["unique_sep_objects"]
            truly_unknown_coords = []

            # Get flux values if available
            if "sep_objects" in context and len(unique_objects) > 0:
                # Extract flux from context for the unique objects
                sep_objects = context["sep_objects"]
                unique_flux = context.get("sep_flux", [])

                if len(unique_flux) == 0 and "sep_flux" in context:
                    # If sep_flux exists but isn't paired with unique objects
                    unique_flux = context["sep_flux"]
            else:
                unique_flux = np.ones(len(unique_objects))  # Default if no flux info

            truly_unknown = []
            search_radius = 15  # arcsec, increased for better matching

            self.logger.info(f"Verifying {len(unique_objects)} SExtractor-unique objects against catalogs")

            # Track objects for detailed logging
            identified_as = {}

            # Check each unique object against astronomical catalogs
            for i, (x_pixel, y_pixel) in enumerate(unique_objects):
                try:
                    # Get flux for this object
                    flux_value = None
                    if isinstance(unique_flux, np.ndarray) and i < len(unique_flux):
                        flux_value = unique_flux[i]

                    # Skip very dim objects (likely noise or sky fragments)
                    if flux_value is not None and flux_value < np.median(unique_flux) * 0.5:
                        self.logger.debug(
                            f"Skipping dim object at ({x_pixel:.1f},{y_pixel:.1f}) with flux {flux_value:.2f}")
                        continue

                    # Convert pixel coordinates to sky coordinates
                    ra, dec = wcs.all_pix2world([[x_pixel, y_pixel]], 1)[0]

                    # Query catalogs for this position with larger search radius
                    self.logger.debug(f"Querying catalogs for object at (RA,Dec)=({ra:.6f}°,{dec:.6f}°)")
                    results = self.catalog.query_all(ra, dec, radius_arcsec=search_radius)

                    if not results:
                        # No catalog matches - truly unknown
                        self.logger.info(
                            f"Object at ({x_pixel:.1f},{y_pixel:.1f}) (RA,Dec)=({ra:.6f}°,{dec:.6f}°) is truly unknown")
                        truly_unknown.append((x_pixel, y_pixel))
                        identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = "unknown"
                        truly_unknown.append((x_pixel, y_pixel))
                        truly_unknown_coords.append({
                            "pixel_x": x_pixel,
                            "pixel_y": y_pixel,
                            "ra": ra,
                            "dec": dec,
                            "ra_formatted": self._format_ra(ra),
                            "dec_formatted": self._format_dec(dec)
                        })
                    else:
                        # Found in catalogs
                        catalog_names = [name for name, _ in results]
                        self.logger.debug(f"Object at ({x_pixel:.1f},{y_pixel:.1f}) found in catalogs: {catalog_names}")
                        identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = ",".join(catalog_names)
                except Exception as e:
                    self.logger.warning(f"Error processing object at ({x_pixel:.1f},{y_pixel:.1f}): {e}")
                    # Skip objects that cause errors
                    identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = f"error: {str(e)}"

            context["truly_unknown_objects"] = truly_unknown
            context["truly_unknown_coords"] = truly_unknown_coords
            context["object_identifications"] = identified_as
            self.logger.info(f"Found {len(truly_unknown)} truly unknown objects after catalog verification")

            # Create visualization of truly unknown objects
            if truly_unknown and "image_path" in context:
                highlighter = ImageHighlighter(context["image_path"])
                highlighter.highlight_points(truly_unknown, radius=12, color="yellow")

                output_path = os.path.splitext(context["image_path"])[0] + "_truly_unknown.jpg"
                highlighter.save(output_path)
                context["truly_unknown_path"] = output_path
                self.logger.info(f"Saved truly unknown objects image to {output_path}")

            return context

        except Exception as e:
            self.logger.error(f"Error in catalog verification: {str(e)}")
            return context

    def _format_ra(self, ra):
        """Format Right Ascension in hours:minutes:seconds"""
        hours = int(ra / 15)  # Convert degrees to hours (RA is traditionally in hours)
        minutes = int((ra / 15 - hours) * 60)
        seconds = ((ra / 15 - hours) * 60 - minutes) * 60
        return f"{hours:02d}h {minutes:02d}m {seconds:05.2f}s"

    def _format_dec(self, dec):
        """Format Declination in degrees:arcminutes:arcseconds"""
        sign = "+" if dec >= 0 else "-"
        dec_abs = abs(dec)
        degrees = int(dec_abs)
        arcminutes = int((dec_abs - degrees) * 60)
        arcseconds = ((dec_abs - degrees) * 60 - arcminutes) * 60
        return f"{sign}{degrees:02d}° {arcminutes:02d}' {arcseconds:05.2f}\""