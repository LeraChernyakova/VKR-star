import time

from astropy.coordinates import SkyCoord, get_body, solar_system_ephemeris
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
        self.logger.info(self.service_name, "CelestialCatalogAdapter initialized")

        self.vizier = Vizier(columns=["_RAJ2000", "_DEJ2000", "Bmag", "Vmag", "rmag"])
        self.vizier.ROW_LIMIT = 100
        self.simbad = Simbad
        self.simbad.add_votable_fields('flux(V)', 'flux(B)')
        self.observer_location = observer_location

        self.solar_system_bodies = ['mercury', 'venus', 'mars', 'jupiter',
                                    'saturn', 'uranus', 'neptune', 'pluto']

        self.cache = {}
        self.cache_expiry = 3600
        self.cache_timestamp = time.time()

    def query_by_coordinates(self, ra, dec, radius_arcsec=10):
        cache_key = f"{ra:.5f}_{dec:.5f}_{radius_arcsec}"
        if cache_key in self.cache:
            self.logger.debug(self.service_name, f"Используем кешированный результат для {cache_key}")
            return self.cache[cache_key]

        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        self._query_standard_catalogs(coord, radius, results)

        self._check_solar_system_bodies(coord, radius * 2, results)

        self._query_mpc(coord, radius, results)

        self.cache[cache_key] = results

        current_time = time.time()
        if current_time - self.cache_timestamp > self.cache_expiry:
            self.cache = {}
            self.cache_timestamp = current_time

        return results

    def query_region(self, center_ra, center_dec, radius_deg=0.5):
        coord = SkyCoord(ra=center_ra * u.deg, dec=center_dec * u.deg, frame="icrs")
        radius = radius_deg * u.deg

        results_map = {}

        try:
            gaia_results = self.vizier.query_region(coord, radius=radius, catalog="I/355/gaiadr3")

            if gaia_results and len(gaia_results) > 0:
                self.logger.info(self.service_name, f"Найдено {len(gaia_results[0])} объектов Gaia в области")
                for row in gaia_results[0]:
                    ra = float(row['_RAJ2000'])
                    dec = float(row['_DEJ2000'])
                    key = (ra, dec)
                    if key in results_map:
                        results_map[key].append(("gaia", row))
                    else:
                        results_map[key] = [("gaia", row)]
            else:
                self.logger.debug(self.service_name, "Объектов Gaia в области не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса каталога Gaia: {e}")

        try:
            usno_results = self.vizier.query_region(coord, radius=radius, catalog="I/284/out")

            if usno_results and len(usno_results) > 0:
                for row in usno_results[0]:
                    ra = float(row['_RAJ2000'])
                    dec = float(row['_DEJ2000'])
                    key = (ra, dec)
                    if key in results_map:
                        results_map[key].append(("usno", row))
                    else:
                        results_map[key] = [("usno", row)]
            else:
                self.logger.debug(self.service_name, "Объектов USNO в области не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса каталога USNO: {e}")

        try:
            simbad_results = self.simbad.query_region(coord, radius=radius)

            if simbad_results and len(simbad_results) > 0:
                self.logger.info(self.service_name, f"Найдено {len(simbad_results)} объектов SIMBAD в области")
                for row in simbad_results:
                    try:
                        if 'RA' in row.colnames and 'DEC' in row.colnames:
                            simbad_coord = SkyCoord(ra=row['RA'], dec=row['DEC'], unit=(u.hourangle, u.deg))
                            ra = float(simbad_coord.ra.deg)
                            dec = float(simbad_coord.dec.deg)
                            key = (ra, dec)
                            if key in results_map:
                                results_map[key].append(("simbad", row))
                            else:
                                results_map[key] = [("simbad", row)]
                    except Exception as inner_e:
                        self.logger.warning(self.service_name, f"Ошибка обработки данных SIMBAD: {inner_e}")
            else:
                self.logger.debug(self.service_name, "Объектов SIMBAD в области не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса базы SIMBAD: {e}")

        try:
            self.logger.debug(self.service_name, "Проверка астероидов в области")
            if hasattr(MPC, 'query_objects_in_sky'):
                mpc_table = MPC.query_objects_in_sky(
                    coord.ra.deg, coord.dec.deg,
                    radius=radius_deg,
                    limit=100
                )

                if mpc_table and len(mpc_table) > 0:
                    for row in mpc_table:
                        ra = float(row['ra'])
                        dec = float(row['dec'])
                        key = (ra, dec)
                        if key in results_map:
                            results_map[key].append(("mpc_asteroids", row))
                        else:
                            results_map[key] = [("mpc_asteroids", row)]
            else:
                self.logger.warning(self.service_name, "Метод query_objects_in_sky в MPC не доступен")
        except Exception as e:
            self.logger.warning(self.service_name, f"Ошибка запроса MPC по астероидам: {e}")

        try:
            self.logger.debug(self.service_name, "Проверка тел Солнечной системы")

            try:
                import jplephem
                has_jplephem = True
            except ImportError:
                has_jplephem = False
                self.logger.warning(self.service_name,
                                    "Пакет jplephem не установлен, пропускаем проверку тел Солнечной системы")

            if has_jplephem:
                current_time = Time.now()
                with solar_system_ephemeris.set('jpl'):
                    for body in self.solar_system_bodies:
                        try:
                            body_coord = get_body(body, current_time, self.observer_location)
                            separation = coord.separation(body_coord)

                            if separation < radius:
                                ra = float(body_coord.ra.deg)
                                dec = float(body_coord.dec.deg)
                                key = (ra, dec)
                                if key in results_map:
                                    results_map[key].append(("solar_system", {"body": body}))
                                else:
                                    results_map[key] = [("solar_system", {"body": body})]
                        except Exception as e:
                            self.logger.warning(self.service_name, f"Ошибка при проверке тела {body}: {e}")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка при проверке тел Солнечной системы: {e}")

        self.logger.info(self.service_name, f"Всего найдено объектов в области: {len(results_map)}")
        return results_map

    def _query_standard_catalogs(self, coord, radius, results):
        try:
            gaia = self.vizier.query_region(coord, radius=radius, catalog="I/355/gaiadr3")
            if gaia and len(gaia) > 0 and len(gaia[0]) > 0:
                self.logger.info(self.service_name, f"Найдено {len(gaia[0])} совпадений в каталоге Gaia")
                results.append(("gaia", gaia[0]))
            else:
                self.logger.debug(self.service_name, "Совпадений в каталоге Gaia не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса каталога Gaia: {e}")

        try:
            self.logger.debug(self.service_name, "Запрос каталога USNO-B1.0")
            usno = self.vizier.query_region(coord, radius=radius, catalog="I/284/out")
            if usno and len(usno) > 0 and len(usno[0]) > 0:
                self.logger.info(self.service_name, f"Найдено {len(usno[0])} совпадений в каталоге USNO-B1.0")
                results.append(("usno", usno[0]))
            else:
                self.logger.debug(self.service_name, "Совпадений в каталоге USNO-B1.0 не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса каталога USNO: {e}")

        try:
            self.logger.debug(self.service_name, "Запрос базы данных SIMBAD")
            simbad = self.simbad.query_region(coord, radius=radius)
            if simbad and len(simbad) > 0:
                self.logger.info(self.service_name, f"Найдено {len(simbad)} совпадений в базе SIMBAD")
                results.append(("simbad", simbad))
            else:
                self.logger.debug(self.service_name, "Совпадений в базе SIMBAD не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса базы SIMBAD: {e}")

    def _check_solar_system_bodies(self, coord, radius, results):
        try:
            current_time = Time.now()
            self.logger.debug(self.service_name, f"Проверка тел солнечной системы на момент: {current_time}")

            with solar_system_ephemeris.set('jpl'):
                for body_name in self.solar_system_bodies:
                    try:
                        body_coord = get_body(body_name, current_time)
                        separation = coord.separation(body_coord)

                        if separation < radius:
                            self.logger.info(
                                self.service_name,
                                f"Найдено тело солнечной системы: {body_name} на расстоянии {separation.arcsec:.2f} угл.сек"
                            )
                            results.append(("solar_system", {
                                "body": body_name,
                                "separation_arcsec": separation.arcsec,
                                "ra": body_coord.ra.deg,
                                "dec": body_coord.dec.deg
                            }))
                    except Exception as e:
                        self.logger.warning(self.service_name, f"Ошибка при проверке {body_name}: {e}")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка при проверке тел солнечной системы: {e}")

    def _query_mpc(self, coord, radius, results):
        try:
            self.logger.debug(self.service_name, "Запрос в Minor Planet Center")

            radius_deg = radius.to(u.deg).value

            try:
                mpc_table = MPC.query_objects_in_sky(
                    coord.ra.deg, coord.dec.deg,
                    radius=radius_deg,
                    limit=20
                )

                if mpc_table and len(mpc_table) > 0:
                    self.logger.info(self.service_name, f"Найдено {len(mpc_table)} совпадений в базе MPC")
                    results.append(("mpc_asteroids", mpc_table))
                else:
                    self.logger.debug(self.service_name, "Астероидов в базе MPC не найдено")
            except Exception as e:
                self.logger.warning(self.service_name, f"Ошибка запроса MPC по астероидам: {e}")

            try:
                comet_table = MPC.query_objects_in_comet_groups(
                    coord.ra.deg, coord.dec.deg,
                    radius=radius_deg,
                    limit=20
                )

                if comet_table and len(comet_table) > 0:
                    self.logger.info(self.service_name, f"Найдено {len(comet_table)} комет в базе MPC")
                    results.append(("mpc_comets", comet_table))
                else:
                    self.logger.debug(self.service_name, "Комет в базе MPC не найдено")
            except Exception as e:
                self.logger.warning(self.service_name, f"Ошибка запроса MPC по кометам: {e}")

        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса Minor Planet Center: {e}")

