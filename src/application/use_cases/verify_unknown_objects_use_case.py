from src.infrastructure.utils.logger import Logger


class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog_service = catalog_service
        self.logger = Logger()

    def execute(self, image_path, pixel_coordinates, wcs):
        try:
            sky_coords = []
            for x_pixel, y_pixel in pixel_coordinates:
                ra, dec = wcs.all_pix2world(x_pixel, y_pixel, 0)
                sky_coords.append({
                    "pixel_x": x_pixel,
                    "pixel_y": y_pixel,
                    "ra": ra,
                    "dec": dec
                })



        except Exception as e:
            self.logger.error(self.service_name,f"Error in object verification: {str(e)}")
            return {"error": str(e)}