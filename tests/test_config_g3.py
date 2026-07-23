"""Pruebas de la configuración del proyecto Grupo 3."""

import unittest

from orbital_compute import config_g3


class TestConfigG3(unittest.TestCase):
    """Valida los parámetros fundamentales del proyecto."""

    def test_number_of_satellites(self) -> None:
        self.assertEqual(config_g3.NUM_SATELLITES, 3)

    def test_satellite_identifiers(self) -> None:
        self.assertEqual(len(config_g3.SATELLITE_IDS), 3)
        self.assertIn(config_g3.LEADER_ID, config_g3.SATELLITE_IDS)

    def test_orbit_is_leo(self) -> None:
        self.assertGreater(config_g3.ORBIT_ALTITUDE_KM, 160.0)
        self.assertLess(config_g3.ORBIT_ALTITUDE_KM, 2000.0)

    def test_isl_frequency_is_high_frequency(self) -> None:
        self.assertGreater(config_g3.ISL_FREQUENCY_GHZ, 20.0)

    def test_energy_thresholds(self) -> None:
        self.assertGreater(config_g3.INITIAL_SOC, config_g3.MINIMUM_SOC)
        self.assertGreater(
            config_g3.MINIMUM_SOC,
            config_g3.CRITICAL_SOC,
        )

    def test_time_step_is_positive(self) -> None:
        self.assertGreater(config_g3.TIME_STEP_S, 0.0)


if __name__ == "__main__":
    unittest.main()