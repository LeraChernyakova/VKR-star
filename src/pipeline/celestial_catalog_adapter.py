from astropy.coordinates import SkyCoord, get_body, solar_system_ephemeris
import astropy.units as u
from astropy.time import Time
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astroquery.mpc import MPC
from src.utils.logger import Logger


class CelestialCatalogAdapter:
    def __init__(self, observer_location="500"):
        self.vizier = Vizier(columns=["_RAJ2000", "_DEJ2000", "Bmag", "Vmag", "rmag"])
        self.vizier.ROW_LIMIT = 100
        self.simbad = Simbad
        self.simbad.add_votable_fields('flux(V)', 'flux(B)')
        self.observer_location = observer_location
        self.logger = Logger()
        self.logger.info("CelestialCatalogAdapter initialized")

        # Solar system bodies to check (including Mars)
        self.solar_system_bodies = ['mercury', 'venus', 'mars', 'jupiter',
                                    'saturn', 'uranus', 'neptune', 'pluto']

    def query_all(self, ra, dec, radius_arcsec=10):
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        # Query standard catalogs
        self._query_standard_catalogs(coord, radius, results)

        # Check against solar system bodies with larger search radius for planets
        self._check_solar_system_bodies(coord, radius * 2, results)

        # Query Minor Planet Center for asteroids and comets
        self._query_mpc(coord, radius, results)

        self.logger.info(f"Query complete. Found objects in {len(results)} catalogs/sources")
        return results

    def _query_standard_catalogs(self, coord, radius, results):
        # Query Gaia DR3
        try:
            self.logger.debug("Querying Gaia DR3 catalog")
            gaia = self.vizier.query_region(coord, radius=radius, catalog="I/355/gaiadr3")
            if gaia and len(gaia) > 0 and len(gaia[0]) > 0:
                self.logger.info(f"Found {len(gaia[0])} matches in Gaia catalog")
                results.append(("gaia", gaia[0]))
            else:
                self.logger.debug("No matches found in Gaia catalog")
        except Exception as e:
            self.logger.error(f"Error querying Gaia catalog: {e}")

        # Query USNO-B1.0 (deeper catalog for faint stars)
        try:
            self.logger.debug("Querying USNO-B1.0 catalog")
            usno = self.vizier.query_region(coord, radius=radius, catalog="I/284/out")
            if usno and len(usno) > 0 and len(usno[0]) > 0:
                self.logger.info(f"Found {len(usno[0])} matches in USNO-B1.0 catalog")
                results.append(("usno", usno[0]))
            else:
                self.logger.debug("No matches found in USNO-B1.0 catalog")
        except Exception as e:
            self.logger.error(f"Error querying USNO catalog: {e}")

        # Query SIMBAD for non-stellar objects
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

    def _check_solar_system_bodies(self, coord, radius, results):
        try:
            # Get current time
            current_time = Time.now()
            self.logger.debug(f"Checking solar system bodies at time: {current_time}")

            # Use the JPL ephemeris for higher accuracy
            with solar_system_ephemeris.set('jpl'):
                # Check each major solar system body
                for body_name in self.solar_system_bodies:
                    try:
                        body_coord = get_body(body_name, current_time)
                        separation = coord.separation(body_coord)

                        if separation < radius:
                            self.logger.info(
                                f"Found solar system body match: {body_name} at separation {separation.arcsec:.2f} arcsec")
                            results.append(("solar_system", {
                                "body": body_name,
                                "separation_arcsec": separation.arcsec,
                                "ra": body_coord.ra.deg,
                                "dec": body_coord.dec.deg
                            }))
                    except Exception as e:
                        self.logger.warning(f"Error checking {body_name}: {e}")
        except Exception as e:
            self.logger.error(f"Error checking solar system bodies: {e}")

    def _query_mpc(self, coord, radius, results):
        try:
            self.logger.debug("Querying Minor Planet Center")

            # Convert radius to degrees for MPC query
            radius_deg = radius.to(u.deg).value

            # Query MPC for asteroids
            try:
                mpc_table = MPC.query_objects_in_sky(
                    coord.ra.deg, coord.dec.deg,
                    radius=radius_deg,
                    limit=20
                )

                if mpc_table and len(mpc_table) > 0:
                    self.logger.info(f"Found {len(mpc_table)} matches in MPC database")
                    results.append(("mpc_asteroids", mpc_table))
                else:
                    self.logger.debug("No asteroid matches found in MPC database")
            except Exception as e:
                self.logger.warning(f"Error querying MPC for asteroids: {e}")

            # Also check comets
            try:
                comet_table = MPC.query_objects_in_comet_groups(
                    coord.ra.deg, coord.dec.deg,
                    radius=radius_deg,
                    limit=20
                )

                if comet_table and len(comet_table) > 0:
                    self.logger.info(f"Found {len(comet_table)} comet matches in MPC database")
                    results.append(("mpc_comets", comet_table))
                else:
                    self.logger.debug("No comet matches found in MPC database")
            except Exception as e:
                self.logger.warning(f"Error querying MPC for comets: {e}")

        except Exception as e:
            self.logger.error(f"Error querying Minor Planet Center: {e}")