import os

from src.infrastructure.utils.image_highlighter import ImageHighlighter
from src.infrastructure.service.object_comparison_service import ObjectComparisonService

class AnalysisController:
    def __init__(self, select_image_use_case, calibrate_image_use_case,
                 detect_objects_use_case, verify_objects_use_case, process_image_use_case):
        self.select_image_use_case = select_image_use_case
        self.calibrate_image_use_case = calibrate_image_use_case
        self.detect_objects_use_case = detect_objects_use_case
        self.verify_objects_use_case = verify_objects_use_case
        self.process_image_use_case = process_image_use_case

    def select_image(self):
        return self.select_image_use_case.execute()

    def analyze_image(self, image_path, status_callback=None):
        try:
            if status_callback:
                status_callback("Калибровка изображения...", "blue")

            result = self.process_image_use_case.execute(
                image_path,
                self.calibrate_image_use_case,
                self.detect_objects_use_case
            )

            sep_result = result.get("detection", {})
            astrometry_result = result.get("astrometry", {})

            sep_coords = sep_result.get("pixel_coords", [])
            astro_coords = astrometry_result.get("pixel_coords", [])
            wcs = astrometry_result.get("wcs")

            comparison_service = ObjectComparisonService()
            unique_coords = comparison_service.find_unique_objects(sep_coords, astro_coords, match_threshold=10)

            if status_callback:
                status_callback("Сравнение с данными из астрономических каталогов...", "blue")

            verify = self.verify_objects_use_case.execute(
                image_path, unique_coords, wcs
            )

            unknown = verify.get("unknown_objects", [])
            points = [(o.get("x"), o.get("y")) for o in unknown]

            truly_unknown_coords = []
            for obj in unknown:
                x, y = obj.get("x"), obj.get("y")
                if wcs:
                    ra, dec = wcs.all_pix2world([[x, y]], 0)[0]

                    from astropy.coordinates import SkyCoord
                    import astropy.units as u

                    coords = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
                    ra_str = coords.ra.to_string(unit=u.hour, sep='h ', precision=2, pad=True)
                    dec_str = coords.dec.to_string(sep='° ', precision=2, alwayssign=True, pad=True)

                    truly_unknown_coords.append({
                        "x": x,
                        "y": y,
                        "ra": ra,
                        "dec": dec,
                        "ra_str": ra_str,
                        "dec_str": dec_str
                    })

            highlighter = ImageHighlighter(image_path)
            highlighter.highlight_points(points, radius=8, color="yellow")
            base, ext = os.path.splitext(image_path)
            vis_path = f"{base}_highlighted{ext}"
            highlighter.save(vis_path)

            return {
                "visualization_path": vis_path,
                "truly_unknown_coords": truly_unknown_coords
            }

        except Exception as e:
            return {"error": str(e)}
