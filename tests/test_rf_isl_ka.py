"""Pruebas del enlace inter-satélite RF en banda Ka."""

import math
import unittest

from orbital_compute.rf_isl_ka import (
    RFISLKa,
    ber_bpsk_qpsk,
    free_space_path_loss_db,
    noise_density_dbw_hz,
    watts_to_dbw,
)


class TestRFISLKa(unittest.TestCase):
    """Valida el balance de enlace RF del Grupo 3."""

    def test_watts_to_dbw(self) -> None:
        self.assertAlmostEqual(
            watts_to_dbw(1.0),
            0.0,
            places=12,
        )

        self.assertAlmostEqual(
            watts_to_dbw(2.0),
            3.0103,
            places=4,
        )

    def test_fspl_at_1_km_and_28_ghz(self) -> None:
        loss = free_space_path_loss_db(
            distance_km=1.0,
            frequency_ghz=28.0,
        )

        self.assertGreater(loss, 121.0)
        self.assertLess(loss, 122.0)

    def test_doubling_distance_adds_six_db(self) -> None:
        loss_1 = free_space_path_loss_db(10.0, 28.0)
        loss_2 = free_space_path_loss_db(20.0, 28.0)

        self.assertAlmostEqual(
            loss_2 - loss_1,
            20.0 * math.log10(2.0),
            places=10,
        )

    def test_noise_density_at_500_k(self) -> None:
        noise_density = noise_density_dbw_hz(500.0)

        self.assertGreater(noise_density, -202.0)
        self.assertLess(noise_density, -201.0)

    def test_nominal_formation_link_is_available(self) -> None:
        link = RFISLKa()
        result = link.evaluate(distance_km=1.0)

        self.assertTrue(result.link_available)
        self.assertGreater(result.link_margin_db, 0.0)
        self.assertLess(result.ber, 1.0e-6)

    def test_long_distance_link_is_unavailable(self) -> None:
        link = RFISLKa()
        result = link.evaluate(distance_km=1000.0)

        self.assertFalse(result.link_available)
        self.assertLess(result.link_margin_db, 0.0)

    def test_ebn0_equation_is_consistent(self) -> None:
        link = RFISLKa()
        result = link.evaluate(distance_km=10.0)

        expected_ebn0 = (
            result.carrier_to_noise_density_dbhz
            - 10.0 * math.log10(link.bitrate_bps)
        )

        self.assertAlmostEqual(
            result.ebn0_db,
            expected_ebn0,
            places=12,
        )

    def test_ber_decreases_when_ebn0_increases(self) -> None:
        ber_low = ber_bpsk_qpsk(0.0)
        ber_high = ber_bpsk_qpsk(10.0)

        self.assertGreater(ber_low, ber_high)
        self.assertGreaterEqual(ber_high, 0.0)
        self.assertLessEqual(ber_low, 0.5)

    def test_propagation_delay_at_1_km(self) -> None:
        result = RFISLKa().evaluate(distance_km=1.0)

        self.assertAlmostEqual(
            result.propagation_delay_s,
            3.3356409519815205e-6,
            places=12,
        )


if __name__ == "__main__":
    unittest.main()