from astropy.io import fits
from astropy.wcs import WCS
from src.domain.interfaces.object_classification_service import IObjectClassificationService
from src.infrastructure.utils.logger import Logger


def _determine_object_class(catalog_results):
    for catalog_name, data in catalog_results:
        if catalog_name == "simbad":
            return data[0]["OTYPE"] if "OTYPE" in data.colnames else "star"
        elif catalog_name == "solar_system":
            return data["body"]
        elif catalog_name == "mpc_asteroids":
            return "asteroid"
        elif catalog_name == "mpc_comets":
            return "comet"

    return "star"


class ObjectClassificationService(IObjectClassificationService):
    def __init__(self, catalog_service):
        self.service_name = "ObjectClassificationService"
        self.catalog_service = catalog_service
        self.logger = Logger()

    def classify_objects(self, objects_data):
        try:
            if "wcs_path" not in objects_data or "pixel_coords" not in objects_data:
                self.logger.error(self.service_name,"Missing required data for classification")
                return {"error": "Missing required data"}

            with fits.open(objects_data["wcs_path"]) as hdul:
                wcs = WCS(hdul[0].header)

            objects_with_class = []

            for x, y in objects_data["pixel_coords"]:
                ra, dec = wcs.all_pix2world([[x, y]], 1)[0]

                catalog_results = self.catalog_service.query_by_coordinates(ra, dec, 15)

                if not catalog_results:
                    object_class = "unknown"
                else:
                    object_class = _determine_object_class(catalog_results)

                objects_with_class.append({
                    "pixel_x": x,
                    "pixel_y": y,
                    "ra": ra,
                    "dec": dec,
                    "class": object_class
                })

            return {"classified_objects": objects_with_class}

        except Exception as e:
            self.logger.error(self.service_name,f"Error in object classification: {str(e)}")
            return {"error": str(e)}

