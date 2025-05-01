from src.infrastructure.utils.logger import Logger
from src.infrastructure.utils.image_highlighter import ImageHighlighter
import os
from astropy.coordinates import SkyCoord
from PIL import Image
import astropy.units as u
from astropy.time import Time
import datetime
import numpy as np


class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog = catalog_service
        self.logger = Logger()

    def execute(self, image_path, pixel_coords, wcs, match_radius_arcsec=5):
        self.logger.info(self.service_name, f"Проверка {len(pixel_coords)} кандидатов")

        filtered = []
        min_pixels = 5
        max_axis_ratio = 4.0
        margin = 5
        min_snr = 2.0

        img = Image.open(image_path)
        width, height = img.size

        sorted_objects = sorted(pixel_coords, key=lambda obj: obj.get('flux', 0), reverse=True)

        fluxes = np.array([p.get('flux', 0) for p in sorted_objects])
        if fluxes.size > 0:
            flux_thresh = np.median(fluxes) * 0.2  # Снижено с 0.4 до 0.2

        else:
            flux_thresh = 0

        for obj in sorted_objects:
            x, y = obj.get('x', 0), obj.get('y', 0)

            if x < margin or y < margin or x > width - margin or y > height - margin:
                continue

            if obj.get('npix', 0) < min_pixels:
                continue

            if obj.get('flux', 0) < flux_thresh:
                continue

            a, b = obj.get('a', 1), obj.get('b', 0.1)
            if a / max(b, 0.001) > max_axis_ratio:
                continue

            # Сделаем проверку по SNR опциональной, если значения доступны
            peak = obj.get('peak', 0)
            background_rms = obj.get('background_rms', 0)
            if background_rms > 0 and peak / background_rms < min_snr:
                continue

            filtered.append(obj)

        filtered_points = [(obj.get("x"), obj.get("y")) for obj in filtered]
        highlighter = ImageHighlighter(image_path)
        highlighter.highlight_points(filtered_points, radius=8, color="green")
        base, ext = os.path.splitext(image_path)
        filtered_vis_path = f"{base}_filtered{ext}"
        highlighter.save(filtered_vis_path)

        unknown = []
        for obj in filtered:
            ra, dec = wcs.all_pix2world([[obj['x'], obj['y']]], 0)[0]
            results = self.catalog.query_all(ra, dec, radius_arcsec=match_radius_arcsec)
            if not results:
                unknown.append(obj)

        self.logger.info(self.service_name,
                         f"Из {len(pixel_coords)} кандидатов отфильтровано {len(filtered)}, из них {len(unknown)} неизвестных")

        return {"unknown_objects": unknown, "unknown_count": len(unknown)}
