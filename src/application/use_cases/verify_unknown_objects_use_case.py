from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter
import os


class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service, object_comparison_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog = catalog_service
        self.comparison_service = object_comparison_service
        self.logger = Logger()

    def execute(self, image_path, sep_coords, astro_coords, wcs, match_radius_arcsec=5):
        unique_coords = self.comparison_service.find_unique_objects(
            sep_coords, astro_coords, match_threshold=10
        )

        pixel_xy = [(obj.get("x"), obj.get("y")) for obj in unique_coords]
        highlighter = ImageHighlighter(image_path)
        highlighter.highlight_points(pixel_xy, radius=8, color="green")
        base, ext = os.path.splitext(image_path)
        filtered_vis_path = f"{base}_filtered{ext}"
        highlighter.save(filtered_vis_path)

        world = wcs.all_pix2world(pixel_xy, 0)

        unknown = []

        for i, obj in enumerate(unique_coords):
            ra, dec = world[i]

            results = self.catalog.find_object_match(ra, dec, radius_arcsec=match_radius_arcsec)

            if not results:
                unknown.append(obj)

        return {
            "unknown_objects": unknown,
            "unknown_count": len(unknown),
            "filtered_image_path": filtered_vis_path
        }