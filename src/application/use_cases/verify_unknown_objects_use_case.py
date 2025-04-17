from astropy.wcs import WCS
from astropy.io import fits
import os
import warnings
from astropy.wcs import FITSFixedWarning
from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter


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

            truly_unknown = []
            truly_unknown_coords = []
            identified_as = {}

            for i, (x_pixel, y_pixel) in enumerate(pixel_coordinates):
                ra, dec = wcs.all_pix2world([[x_pixel, y_pixel]], 1)[0]

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
                highlighter.highlight_points(truly_unknown, radius=12, color="yellow")

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