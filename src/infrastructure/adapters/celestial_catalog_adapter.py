import warnings
import astropy.units as u

from astropy.time import Time
from astroquery.mpc import MPC
from functools import lru_cache
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astroquery.exceptions import NoResultsWarning
from src.infrastructure.utils.logger import Logger
from typing import Dict, List, Tuple, Any, Optional
from src.domain.interfaces.catalog_service import ICatalogService
from astropy.coordinates import SkyCoord


class CelestialCatalogAdapter(ICatalogService):
    def __init__(self):
        self.service_name = "CelestialCatalogAdapter"
        self.logger = Logger()

        self.vizier = Vizier(
            columns=["_RAJ2000", "_DEJ2000", "Bmag", "Vmag", "rmag", "imag"],
            row_limit=-1
        )

        self.simbad = Simbad
        self.simbad.add_votable_fields('flux(V)', 'flux(B)', 'flux(R)', 'otype', 'ids')

    def find_object_match(self, ra, dec, radius_arcsec=5, early_exit=True):
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        radius = radius_arcsec * u.arcsec
        results = []

        catalogs = [
            ("gaia", "I/355/gaiadr3"),
            ("usno", "I/284/out"),
            ("ps1", "II/349/ps1")
        ]

        for name, catalog in catalogs:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=NoResultsWarning)
                    tbl = self.vizier.query_region(coord, radius=radius, catalog=catalog)
                    if tbl and len(tbl) > 0 and len(tbl[0]) > 0:
                        results.extend([(name, row) for row in tbl[0]])
                        if early_exit and results:
                            return results
            except Exception as e:
                pass

        try:
            if hasattr(MPC, "query_objects_in_sky"):
                mpc = MPC.query_objects_in_sky(coord.ra.deg, coord.dec.deg,
                                               radius=radius.value, limit=20)
                if mpc and len(mpc) > 0:
                    results.extend([("mpc", row) for row in mpc])
                    if early_exit and results:
                        return results
        except Exception:
            pass

        return results