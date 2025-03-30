from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from src.utils.logger import Logger

class CelestialCatalogAdapter:
    def __init__(self, observer_location="500"):
        self.vizier = Vizier(columns=["RA_ICRS", "DE_ICRS", "Gmag"])
        self.vizier.ROW_LIMIT = 50
        self.simbad = Simbad
        self.observer_location = observer_location
        self.logger = Logger()
        self.logger.info("CelestialCatalogAdapter initialized")

    def query_all(self, ra, dec, radius_arcsec=3):
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        self.logger.info(f"Querying catalogs for RA={ra:.6f}°, Dec={dec:.6f}°, radius={radius_arcsec}\"")

        try:
            self.logger.debug("Querying Gaia DR2 catalog")
            gaia = self.vizier.query_region(coord, radius=radius, catalog="I/345/gaia2")
            if gaia and len(gaia) > 0 and len(gaia[0]) > 0:
                self.logger.info(f"Found {len(gaia[0])} matches in Gaia catalog")
                results.append(("gaia", gaia[0]))
            else:
                self.logger.debug("No matches found in Gaia catalog")
        except Exception as e:
            self.logger.error(f"Error querying Gaia catalog: {e}")

        try:
            self.logger.debug("Querying SIMBAD database")
            simbad = self.simbad.query_region(coord, radius=radius)
            if simbad and len(simbad) > 0:
                self.logger.info(f"Found {len(simbad)} matches in SIMBAD database")
                results.append(("simbad", simbad))
            else:
                self.logger.debug("No matches found in SIMBAD database")
        except Exception as e:
            self.logger.error(f"Error querying SIMBAD database: {e}")

        self.logger.info(f"Query complete. Found objects in {len(results)} catalogs")
        return results
