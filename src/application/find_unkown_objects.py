class FindUnknownObjectsUseCase:
    def __init__(self, astrometry_service, detection_service, catalog_service):
        self.astrometry_service = astrometry_service
        self.detection_service = detection_service
        self.catalog_service = catalog_service

    def execute(self, image_path):
        wcs_data = self.astrometry_service.calibrate_image(image_path)

        detected_objects = self.detection_service.detect_objects(image_path)

        unknown_objects = []
        for obj in detected_objects:
            if obj.ra and obj.dec:
                catalog_results = self.catalog_service.query_by_coordinates(
                    obj.ra, obj.dec, 15
                )
                if not catalog_results:
                    unknown_objects.append(obj)

        return unknown_objects