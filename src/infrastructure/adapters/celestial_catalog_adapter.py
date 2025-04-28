import time
import concurrent.futures
from typing import Dict, List, Tuple, Any, Optional

from astropy.coordinates import SkyCoord, get_body, solar_system_ephemeris, EarthLocation
import astropy.units as u
from astropy.time import Time
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astroquery.mpc import MPC

from src.domain.interfaces.catalog_service import ICatalogService
from src.infrastructure.utils.logger import Logger


class CelestialCatalogAdapter(ICatalogService):
    def __init__(self, observer_location="500"):
        self.service_name = "CelestialCatalogAdapter"
        self.logger = Logger()

        self.vizier = Vizier(columns=["_RAJ2000", "_DEJ2000", "Bmag", "Vmag", "rmag", "imag"])
        self.vizier.ROW_LIMIT = 500

        self.simbad = Simbad
        self.simbad.add_votable_fields('flux(V)', 'flux(B)', 'flux(R)', 'otype', 'ids')

        self.solar_system_bodies = [
            'mercury', 'venus', 'mars', 'jupiter', 'saturn',
            'uranus', 'neptune', 'pluto', 'moon', 'sun'
        ]

    def query_region(self, center_ra, center_dec, radius_deg=0.5, observation_time=None):
        coord = SkyCoord(ra=center_ra * u.deg, dec=center_dec * u.deg, frame="icrs")
        radius = radius_deg * u.deg
        results_map = {}

        def query_gaia():
            try:
                results = self.vizier.query_region(coord, radius=radius, catalog="I/355/gaiadr3")
                return "gaia", self._process_vizier_results(results)
            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка запроса Gaia: {e}")
                return "gaia", []

        def query_usno():
            try:
                results = self.vizier.query_region(coord, radius=radius, catalog="I/284/out")
                return "usno", self._process_vizier_results(results)
            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка запроса USNO: {e}")
                return "usno", []

        def query_simbad():
            try:
                results = self.simbad.query_region(coord, radius=radius)
                return "simbad", self._process_simbad_results(results)
            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка запроса SIMBAD: {e}")
                return "simbad", []

        def query_asteroids():
            try:
                if hasattr(MPC, 'query_objects_in_sky'):
                    results = MPC.query_objects_in_sky(coord.ra.deg, coord.dec.deg,
                                                       radius=radius_deg, limit=100)
                    return "mpc", self._process_mpc_results(results)
                return "mpc", []
            except Exception as e:
                self.logger.error(self.service_name, f"Ошибка запроса MPC: {e}")
                return "mpc", []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(query_gaia),
                executor.submit(query_usno),
                executor.submit(query_simbad),
                executor.submit(query_asteroids)
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    source, source_results = future.result()
                    for ra, dec, data in source_results:
                        key = (ra, dec)
                        if key in results_map:
                            results_map[key].append((source, data))
                        else:
                            results_map[key] = [(source, data)]
                except Exception as e:
                    self.logger.error(self.service_name, f"Ошибка при обработке результатов: {e}")

        if observation_time is not None:
            self._add_solar_system_objects(results_map, coord, radius, observation_time)

        self.logger.info(self.service_name, f"Всего найдено объектов в области: {len(results_map)}")

        return results_map

    def _process_vizier_results(self, results):
        processed = []
        if results and len(results) > 0:
            for row in results[0]:
                try:
                    ra = float(row['_RAJ2000'])
                    dec = float(row['_DEJ2000'])
                    processed.append((ra, dec, row))
                except Exception:
                    continue
        return processed

    def _process_simbad_results(self, results):
        processed = []
        if results and len(results) > 0:
            for row in results:
                try:
                    if 'RA' in row.colnames and 'DEC' in row.colnames:
                        simbad_coord = SkyCoord(ra=row['RA'], dec=row['DEC'],
                                                unit=(u.hourangle, u.deg))
                        ra = float(simbad_coord.ra.deg)
                        dec = float(simbad_coord.dec.deg)
                        processed.append((ra, dec, row))
                except Exception:
                    continue
        return processed

    def _process_mpc_results(self, results):
        processed = []
        if results and len(results) > 0:
            for row in results:
                try:
                    ra = float(row['ra'])
                    dec = float(row['dec'])
                    processed.append((ra, dec, row))
                except Exception:
                    continue
        return processed

    def _add_solar_system_objects(self, results_map, coord, radius, time):
        try:
            try:
                import jplephem
                has_jplephem = True
            except ImportError:
                has_jplephem = False
                self.logger.warning(self.service_name,
                                    "Пакет jplephem не установлен, точные координаты планет недоступны")

            if has_jplephem:
                observer_location = None
                with solar_system_ephemeris.set('jpl'):
                    for body in self.solar_system_bodies:
                        try:
                            body_coord = get_body(body, time, observer_location)
                            separation = coord.separation(body_coord)

                            if separation < radius:
                                ra = float(body_coord.ra.deg)
                                dec = float(body_coord.dec.deg)
                                body_info = {
                                    "body": body,
                                    "ra": ra,
                                    "dec": dec,
                                    "separation_arcmin": float(separation.arcmin)
                                }
                                key = (ra, dec)
                                if key in results_map:
                                    results_map[key].append(("solar_system", body_info))
                                else:
                                    results_map[key] = [("solar_system", body_info)]

                        except Exception as e:
                            self.logger.warning(self.service_name, f"Ошибка при проверке тела {body}: {e}")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка при проверке тел Солнечной системы: {e}")