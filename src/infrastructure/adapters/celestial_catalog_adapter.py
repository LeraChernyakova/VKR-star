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

    def query_by_coordinates(self, ra, dec, radius_arcsec=10):
        return self.query_all(ra, dec, radius_arcsec)

    def query_all(self, ra, dec, radius_arcsec=10):
        """
        Запрашивает информацию по всем каталогам для указанных координат
        Возвращает список найденных объектов в формате [(catalog_name, data), ...]
        """
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        # Запрос стандартных каталогов
        self._query_standard_catalogs(coord, radius, results)

        # Проверка на наличие тел солнечной системы
        self._check_solar_system_bodies(coord, radius * 2, results)

        # Запрос в Minor Planet Center на наличие астероидов и комет
        self._query_mpc(coord, radius, results)

        self.logger.info(self.service_name, f"Найдено {len(results)} объектов в каталогах")
        return results

    def _query_standard_catalogs(self, coord, radius, results):
        """Поиск объекта в стандартных звездных каталогах"""
        # Запрос Gaia DR3
        try:
            self.logger.debug(self.service_name, "Запрос каталога Gaia DR3")
            gaia = self.vizier.query_region(coord, radius=radius, catalog="I/355/gaiadr3")
            if gaia and len(gaia) > 0 and len(gaia[0]) > 0:
                self.logger.info(self.service_name, f"Найдено {len(gaia[0])} совпадений в каталоге Gaia")
                results.append(("gaia", gaia[0]))
            else:
                self.logger.debug(self.service_name, "Совпадений в каталоге Gaia не найдено")
        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка запроса каталога Gaia: {e}")

        # Запрос USNO-B1.0 (для более слабых звезд)
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

        # Запрос SIMBAD для нестеллярных объектов
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
        """Проверка на совпадение с телами солнечной системы"""
        try:
            # Получаем текущее время
            current_time = Time.now()
            self.logger.debug(self.service_name, f"Проверка тел солнечной системы на момент: {current_time}")

            # Используем JPL эфемериды для большей точности
            with solar_system_ephemeris.set('jpl'):
                # Проверяем каждое крупное тело солнечной системы
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
        """Запрос в Minor Planet Center для поиска астероидов и комет"""
        try:
            self.logger.debug(self.service_name, "Запрос в Minor Planet Center")

            # Конвертация радиуса в градусы для запроса MPC
            radius_deg = radius.to(u.deg).value

            # Запрос MPC на наличие астероидов
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

            # Также проверяем кометы
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