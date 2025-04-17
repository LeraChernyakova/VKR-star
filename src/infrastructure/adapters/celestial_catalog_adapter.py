from astropy.coordinates import SkyCoord
import astropy.units as u
from src.domain.interfaces.catalog_service import ICatalogService
from src.infrastructure.utils.logger import Logger

class CelestialCatalogAdapter(ICatalogService):
    def __init__(self, observer_location="500"):
        self.service_name = "CelestialCatalogAdapter"
        self.logger = Logger()
        self.logger.info(self.service_name,"CelestialCatalogAdapter initialized")

    def query_by_coordinates(self, ra, dec, radius_arcsec=10):
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        self._query_standard_catalogs(coord, radius, results)
        self._check_solar_system_bodies(coord, radius * 2, results)
        self._query_mpc(coord, radius, results)

        self.logger.info(self.service_name,f"Query complete. Found objects in {len(results)} catalogs/sources")
        return results