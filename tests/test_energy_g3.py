"""Pruebas del sistema energético de los CubeSats G3."""

import unittest

from orbital_compute.energy_g3 import (
    CubeSatEnergySystem,
    EnergyLoads,
    OperatingMode,
)


class TestEnergyG3(unittest.TestCase):
    """Valida batería, consumos y modos de operación."""

    def test_initial_soc(self) -> None:
        system = CubeSatEnergySystem(
            battery_capacity_wh=60.0,
            initial_soc=0.80,
        )

        self.assertAlmostEqual(system.soc, 0.80)
        self.assertAlmostEqual(
            system.battery_energy_wh,
            48.0,
        )

    def test_default_mode_is_normal(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.80)

        self.assertEqual(
            system.mode,
            OperatingMode.NORMAL,
        )

    def test_eclipse_discharges_battery(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.80)
        initial_energy = system.battery_energy_wh

        result = system.step(
            time_step_s=600.0,
            illuminated=False,
            loads=EnergyLoads(
                isl_active=True,
                federated_training_active=True,
            ),
        )

        self.assertLess(
            result.battery_energy_wh,
            initial_energy,
        )

    def test_sunlight_charges_battery(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.50)
        initial_energy = system.battery_energy_wh

        result = system.step(
            time_step_s=600.0,
            illuminated=True,
            loads=EnergyLoads(),
        )

        self.assertGreater(
            result.battery_energy_wh,
            initial_energy,
        )

    def test_battery_does_not_exceed_capacity(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.99)

        for _ in range(20):
            system.step(
                time_step_s=600.0,
                illuminated=True,
                loads=EnergyLoads(
                    housekeeping_active=False,
                    control_active=False,
                ),
            )

        self.assertLessEqual(
            system.battery_energy_wh,
            system.battery_capacity_wh,
        )

    def test_power_save_mode(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.25)

        self.assertEqual(
            system.mode,
            OperatingMode.POWER_SAVE,
        )

    def test_critical_mode(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.10)

        self.assertEqual(
            system.mode,
            OperatingMode.CRITICAL,
        )

    def test_training_not_allowed_with_low_soc(self) -> None:
        system = CubeSatEnergySystem(initial_soc=0.25)

        self.assertFalse(
            system.federated_training_allowed()
        )

    def test_total_load_includes_active_subsystems(self) -> None:
        loads = EnergyLoads(
            housekeeping_active=True,
            control_active=True,
            isl_active=True,
            federated_training_active=True,
        )

        expected_power = (
            8.0
            + 3.0
            + 5.0
            + 12.0
        )

        self.assertAlmostEqual(
            loads.total_power_w(),
            expected_power,
        )


if __name__ == "__main__":
    unittest.main()