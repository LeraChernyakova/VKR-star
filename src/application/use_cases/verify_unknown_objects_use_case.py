from src.infrastructure.utils.logger import Logger

from astropy.coordinates import SkyCoord
from PIL import Image
import astropy.units as u
from astropy.time import Time
import datetime
import numpy as np


def _extract_time(wcs):
    try:
        hdr = wcs.to_header()
        date = hdr.get('DATE-OBS') or hdr.get('DATE')
        return Time(date, format='isot') if date else None
    except:
        return None


class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog = catalog_service
        self.logger = Logger()

    def execute(self, image_path, pixel_coords, wcs, match_radius_arcsec=5):
        self.logger.info(self.service_name, f"Старт проверки {len(pixel_coords)} кандидатов")

        try:
            img = Image.open(image_path)
            width, height = img.size
        except Exception as e:
            self.logger.warning(self.service_name, f"Не удалось загрузить изображение для фильтрации: {e}")
            width = height = None

        fluxes = np.array([p.get('flux', 0) for p in pixel_coords])
        flux_thresh = np.median(fluxes) * 0.5 if fluxes.size else 0
        min_pixels = 12
        max_axis_ratio = 2.5
        margin = 8

        filtered_pixels = []
        for o in pixel_coords:
            x, y = o.get('x', 0), o.get('y', 0)

            if o.get('flag', 0) != 0:
                continue

            if o.get('npix', 0) < min_pixels:
                continue

            if o.get('flux', 0) < flux_thresh:
                continue

            a, b = o.get('a', 1), o.get('b', 1)
            if a / max(b, 1e-3) > max_axis_ratio:
                continue

            if width and height:
                if x < margin or x > width - margin or y < margin or y > height - margin:
                    continue
            filtered_pixels.append(o)

        self.logger.info(self.service_name, f"После фильтрации осталось {len(filtered_pixels)} кандидатов")

        if not filtered_pixels:
            return {"unknown_objects": [], "known_objects": [],
                    "total_count": len(pixel_coords), "unknown_count": 0}

        ras, decs = [], []
        for o in filtered_pixels:
            ra, dec = wcs.all_pix2world([[o['x'], o['y']]], 0)[0]
            ras.append(ra);
            decs.append(dec)
        det_coords = SkyCoord(ra=ras * u.deg, dec=decs * u.deg)

        center = SkyCoord(ra=sum(ras) / len(ras) * u.deg,
                          dec=sum(decs) / len(decs) * u.deg)
        maxsep = max(center.separation(SkyCoord(ra=ra * u.deg, dec=dec * u.deg)).deg
                     for ra, dec in zip(ras, decs)) + 0.05
        catalog_results = self.catalog.query_region(
            center.ra.deg, center.dec.deg,
            radius_deg=maxsep,
            observation_time=_extract_time(wcs)
        )

        cat_ras, cat_decs, cat_meta = [], [], []
        for (ra, dec), entries in catalog_results.items():
            for entry in entries:
                cat_ras.append(ra);
                cat_decs.append(dec);
                cat_meta.append(entry)

        if not cat_ras:
            return {"unknown_objects": filtered_pixels, "unknown_count": len(filtered_pixels)}

        cat_coords = SkyCoord(ra=cat_ras * u.deg, dec=cat_decs * u.deg)

        idx_cat, idx_det, sep2d, _ = cat_coords.search_around_sky(
            det_coords, match_radius_arcsec * u.arcsec
        )

        known_map = {}
        for c_i, d_i, sep in zip(idx_cat, idx_det, sep2d.arcsec):
            if d_i not in known_map or sep < known_map[d_i][0]:
                known_map[d_i] = (sep, cat_meta[c_i])

        known_objs, unknown_objs = [], []
        for i, pc in enumerate(filtered_pixels):
            if i in known_map:
                sep, meta = known_map[i]
                pc.update({"catalog_match": meta, "separation_arcsec": sep})
                known_objs.append(pc)
            else:
                unknown_objs.append(pc)

        self.logger.info(self.service_name,
                         f"Из {len(filtered_pixels)}: "
                         f"{len(unknown_objs)} неизвестных")
        return {
            "unknown_objects": unknown_objs,
            "known_objects": known_objs,
            "total_count": len(pixel_coords),
            "unknown_count": len(unknown_objs)
        }

