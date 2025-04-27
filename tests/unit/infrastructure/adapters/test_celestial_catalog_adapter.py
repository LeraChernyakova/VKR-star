import pytest
from unittest.mock import Mock, patch, MagicMock
import astropy.units as u
from astropy.coordinates import SkyCoord
from src.infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter


class TestCelestialCatalogAdapter:
    def setup_method(self):
        self.adapter = CelestialCatalogAdapter()
        self.test_ra = 10.0
        self.test_dec = 20.0
        self.test_radius = 10.0

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Vizier')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Simbad')
    def test_initialization(self, mock_simbad, mock_vizier):
        adapter = CelestialCatalogAdapter()

        mock_vizier.assert_called_once()

        mock_simbad.add_votable_fields.assert_called()

        assert adapter.observer_location == "500"
        assert len(adapter.solar_system_bodies) > 0

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.CelestialCatalogAdapter._query_standard_catalogs')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.CelestialCatalogAdapter._check_solar_system_bodies')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.CelestialCatalogAdapter._query_mpc')
    def test_query_all(self, mock_query_mpc, mock_check_solar_system, mock_query_standard):
        mock_query_standard.return_value = None
        mock_check_solar_system.return_value = None
        mock_query_mpc.return_value = None

        self.adapter.query_all(self.test_ra, self.test_dec, self.test_radius)

        mock_query_standard.assert_called_once()
        mock_check_solar_system.assert_called_once()
        mock_query_mpc.assert_called_once()

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.CelestialCatalogAdapter.query_all')
    def test_query_by_coordinates(self, mock_query_all):
        mock_query_all.return_value = [("test_catalog", "test_data")]

        result = self.adapter.query_by_coordinates(self.test_ra, self.test_dec, self.test_radius)

        mock_query_all.assert_called_once_with(self.test_ra, self.test_dec, self.test_radius)

        assert result == [("test_catalog", "test_data")]

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Vizier')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Simbad')
    def test_query_standard_catalogs_success(self, mock_simbad, mock_vizier):
        mock_vizier_instance = mock_vizier.return_value
        mock_gaia_result = [MagicMock()]
        mock_gaia_result[0].__len__.return_value = 1
        mock_usno_result = [MagicMock()]
        mock_usno_result[0].__len__.return_value = 1

        mock_vizier_instance.query_region.side_effect = [mock_gaia_result, mock_usno_result]

        mock_simbad_result = MagicMock()
        mock_simbad_result.__len__.return_value = 1
        mock_simbad.query_region.return_value = mock_simbad_result

        coord = SkyCoord(ra=self.test_ra * u.deg, dec=self.test_dec * u.deg)
        radius = self.test_radius * u.arcsec
        results = []

        self.adapter._query_standard_catalogs(coord, radius, results)

        assert len(results) == 3
        assert results[0][0] == "gaia"
        assert results[1][0] == "usno"
        assert results[2][0] == "simbad"

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.get_body')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.solar_system_ephemeris')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Time')
    def test_check_solar_system_bodies_match(self, mock_time, mock_solar_system_ephemeris, mock_get_body):
        mock_time_instance = mock_time.now.return_value

        mock_context = MagicMock()
        mock_solar_system_ephemeris.set.return_value = mock_context

        mock_body_coord = MagicMock()
        mock_body_coord.ra.deg = self.test_ra + 0.0001
        mock_body_coord.dec.deg = self.test_dec + 0.0001

        mock_separation = MagicMock()
        mock_separation.arcsec = 5.0

        mock_coord = MagicMock()
        mock_coord.separation.return_value = mock_separation

        mock_get_body.return_value = mock_body_coord

        results = []
        self.adapter._check_solar_system_bodies(mock_coord, self.test_radius * u.arcsec, results)

        assert len(results) > 0
        assert results[0][0] == "solar_system"

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.MPC')
    def test_query_mpc_success(self, mock_mpc):
        mock_asteroid_table = MagicMock()
        mock_asteroid_table.__len__.return_value = 2
        mock_mpc.query_objects_in_sky.return_value = mock_asteroid_table

        mock_comet_table = MagicMock()
        mock_comet_table.__len__.return_value = 1
        mock_mpc.query_objects_in_comet_groups.return_value = mock_comet_table

        results = []
        self.adapter._query_mpc(
            SkyCoord(ra=self.test_ra * u.deg, dec=self.test_dec * u.deg),
            self.test_radius * u.arcsec,
            results
        )

        assert len(results) == 2
        assert results[0][0] == "mpc_asteroids"
        assert results[1][0] == "mpc_comets"

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Vizier')
    def test_standard_catalogs_exception_handling(self, mock_vizier):
        mock_vizier_instance = mock_vizier.return_value
        mock_vizier_instance.query_region.side_effect = Exception("Test exception")

        coord = SkyCoord(ra=self.test_ra * u.deg, dec=self.test_dec * u.deg)
        radius = self.test_radius * u.arcsec
        results = []

        self.adapter._query_standard_catalogs(coord, radius, results)

        assert len(results) == 0

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.get_body')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.solar_system_ephemeris')
    @patch('src.infrastructure.adapters.celestial_catalog_adapter.Time')
    def test_solar_system_bodies_exception_handling(self, mock_time, mock_solar_system_ephemeris, mock_get_body):
        mock_time.now.side_effect = Exception("Time error")

        results = []
        coord = SkyCoord(ra=self.test_ra * u.deg, dec=self.test_dec * u.deg)

        self.adapter._check_solar_system_bodies(coord, self.test_radius * u.arcsec, results)

        assert len(results) == 0

    @patch('src.infrastructure.adapters.celestial_catalog_adapter.MPC')
    def test_mpc_exception_handling(self, mock_mpc):
        mock_mpc.query_objects_in_sky.side_effect = Exception("MPC error")
        mock_mpc.query_objects_in_comet_groups.side_effect = Exception("MPC comet error")

        results = []
        coord = SkyCoord(ra=self.test_ra * u.deg, dec=self.test_dec * u.deg)

        self.adapter._query_mpc(coord, self.test_radius * u.arcsec, results)

        assert len(results) == 0