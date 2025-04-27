import math

from astropy.wcs import WCS
from astropy.io import fits
import os
import warnings
from astropy.wcs import FITSFixedWarning
from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter


def angular_distance(ra1, dec1, ra2, dec2):
    ra1_rad = math.radians(ra1)
    dec1_rad = math.radians(dec1)
    ra2_rad = math.radians(ra2)
    dec2_rad = math.radians(dec2)

    dlon = ra2_rad - ra1_rad
    dlat = dec2_rad - dec1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(dec1_rad) * math.cos(dec2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return math.degrees(c)

class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog_service = catalog_service
        self.logger = Logger()

    def execute(self, image_path, wcs_path, pixel_coordinates, search_radius=15):
        try:
            self.logger.info(self.service_name,"Verifying {len(pixel_coordinates)} objects against catalogs")

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', FITSFixedWarning)
                with fits.open(wcs_path, ignore_missing_simple=True) as hdul:
                    wcs = WCS(hdul[0].header)

            sky_coords = []
            for x_pixel, y_pixel in pixel_coordinates:
                ra, dec = wcs.all_pix2world([[x_pixel, y_pixel]], 1)[0]
                sky_coords.append((x_pixel, y_pixel, ra, dec))

            ra_values = [c[2] for c in sky_coords]
            dec_values = [c[3] for c in sky_coords]
            center_ra = (max(ra_values) + min(ra_values)) / 2
            center_dec = (max(dec_values) + min(dec_values)) / 2
            radius_deg = max(
                max(ra_values) - min(ra_values),
                max(dec_values) - min(dec_values)
            ) / 2 + 0.1

            catalog_map = self.catalog_service.query_region(center_ra, center_dec, radius_deg)

            truly_unknown = []
            truly_unknown_coords = []
            identified_as = {}

            for x_pixel, y_pixel, ra, dec in sky_coords:
                found = False
                for cat_ra, cat_dec in catalog_map.keys():
                    dist = angular_distance(ra, dec, cat_ra, cat_dec)
                    if dist < search_radius / 3600:
                        found = True
                        catalog_names = [name for name, _ in catalog_map[(cat_ra, cat_dec)]]
                        identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = ",".join(catalog_names)
                        break

                if not found:
                    results = self.catalog_service.query_by_coordinates(ra, dec, radius_arcsec=search_radius)
                    if not results:
                        truly_unknown.append((x_pixel, y_pixel))
                        truly_unknown_coords.append({
                            "pixel_x": x_pixel,
                            "pixel_y": y_pixel,
                            "ra": ra,
                            "dec": dec
                        })
                        identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = "unknown"
                    else:
                        catalog_names = [name for name, _ in results]
                        identified_as[f"{x_pixel:.1f},{y_pixel:.1f}"] = ",".join(catalog_names)

            if truly_unknown and image_path:
                highlighter = ImageHighlighter(image_path)
                highlighter.highlight_points(truly_unknown, radius=12, color="red")

                output_path = os.path.splitext(image_path)[0] + "_truly_unknown.jpg"
                highlighter.save(output_path)

                return {
                    "truly_unknown": truly_unknown,
                    "truly_unknown_coords": truly_unknown_coords,
                    "identifications": identified_as,
                    "visualization_path": output_path
                }

            return {
                "truly_unknown": truly_unknown,
                "truly_unknown_coords": truly_unknown_coords,
                "identifications": identified_as
            }

        except Exception as e:
            self.logger.error(self.service_name,f"Error in object verification: {str(e)}")
            return {"error": str(e)}

    def process(self, data):
        if "image_path" not in data or "wcs_path" not in data or "pixel_coords" not in data:
            self.logger.error(self.service_name,"Недостаточно данных для проверки объектов")
            return {"error": "Недостаточно данных для проверки объектов"}

        return self.execute(
            data["image_path"],
            data["wcs_path"],
            data["pixel_coords"]
        )