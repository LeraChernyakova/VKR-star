import astropy.units as u

from astropy.coordinates import SkyCoord


class AnalysisController:
    def __init__(self, select_image_use_case, process_image_use_case):
        self.select_image_use_case = select_image_use_case
        self.process_image_use_case = process_image_use_case

    def select_image(self):
        return self.select_image_use_case.execute()

    def analyze_image(self, image_path, status_callback=None):
        try:
            if status_callback:
                status_callback("Калибровка изображения...", "blue")

            result = self.process_image_use_case.execute(image_path, status_callback)

            if "error" in result:
                return result

            if status_callback:
                status_callback("Анализ завершен", "green")

            unknown_objects = result.get("unknown_objects", [])
            wcs = result.get("astrometry", {}).get("wcs")

            truly_unknown_coords = []
            if wcs:
                for obj in unknown_objects:
                    x, y = obj.get("x"), obj.get("y")
                    ra, dec = wcs.all_pix2world([[x, y]], 0)[0]
                    coords = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
                    ra_hms = coords.ra.hms
                    ra_str = f"{int(ra_hms.h):02d}h {int(ra_hms.m):02d}m {ra_hms.s:.2f}s"
                    dec_dms = coords.dec.dms
                    sign = '+' if dec_dms.d >= 0 else '-'
                    dec_str = f"{sign}{int(abs(dec_dms.d)):02d}° {int(abs(dec_dms.m)):02d}' {abs(dec_dms.s):.2f}\""

                    truly_unknown_coords.append({
                        "x": x,
                        "y": y,
                        "ra": ra,
                        "dec": dec,
                        "ra_str": ra_str,
                        "dec_str": dec_str
                    })

            return {
                "visualization_path": result.get("visualization_path", ""),
                "truly_unknown_coords": truly_unknown_coords
            }

        except Exception as e:
            return {"error": str(e)}