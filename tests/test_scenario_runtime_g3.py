"""Pruebas del motor temporal de escenarios G3."""

from __future__ import annotations

import unittest

import numpy as np

from orbital_compute import config_g3
from orbital_compute.energy_g3 import (
    CubeSatEnergySystem,
)
from orbital_compute.scenario_runtime_g3 import (
    ScenarioRuntime,
)
from orbital_compute.scenarios_g3 import (
    ScenarioName,
    get_scenario,
)


class TestScenarioRuntimeG3(
    unittest.TestCase
):
    """Valida la activación temporal de las fallas."""

    def make_states(
        self,
    ) -> dict[str, np.ndarray]:
        """Construye estados relativos de prueba."""

        return {
            satellite_id: np.zeros(
                6,
                dtype=float,
            )
            for satellite_id
            in config_g3.SATELLITE_IDS
        }

    def make_energy(
        self,
    ) -> dict[
        str,
        CubeSatEnergySystem,
    ]:
        """Construye sistemas energéticos de prueba."""

        return {
            satellite_id: (
                CubeSatEnergySystem(
                    initial_soc=0.80
                )
            )
            for satellite_id
            in config_g3.SATELLITE_IDS
        }

    def test_low_power_sets_requested_soc(
        self,
    ) -> None:
        """La falla energética debe modificar el SOC."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName.LOW_POWER
            )
        )

        states = self.make_states()
        energy = self.make_energy()

        runtime.update(
            time_s=900.0,
            relative_states=states,
            energy_systems=energy,
        )

        self.assertAlmostEqual(
            energy[
                config_g3.FOLLOWER_2_ID
            ].soc,
            0.18,
        )

    def test_position_offset_is_applied_once(
        self,
    ) -> None:
        """La perturbación no debe aplicarse dos veces."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName
                .FORMATION_DISTURBANCE
            )
        )

        states = self.make_states()
        energy = self.make_energy()

        runtime.update(
            time_s=1200.0,
            relative_states=states,
            energy_systems=energy,
        )

        first_position = states[
            config_g3.FOLLOWER_1_ID
        ][0:3].copy()

        runtime.update(
            time_s=1260.0,
            relative_states=states,
            energy_systems=energy,
        )

        second_position = states[
            config_g3.FOLLOWER_1_ID
        ][0:3].copy()

        np.testing.assert_allclose(
            first_position,
            [
                80.0,
                -120.0,
                40.0,
            ],
        )

        np.testing.assert_allclose(
            second_position,
            first_position,
        )

    def test_link_loss_is_active_only_in_window(
        self,
    ) -> None:
        """La atenuación adicional respeta su duración."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName.ISL_DEGRADATION
            )
        )

        satellite_id = (
            config_g3.FOLLOWER_1_ID
        )

        self.assertEqual(
            runtime.additional_link_loss_db(
                satellite_id,
                899.0,
            ),
            0.0,
        )

        self.assertEqual(
            runtime.additional_link_loss_db(
                satellite_id,
                900.0,
            ),
            35.0,
        )

        self.assertEqual(
            runtime.additional_link_loss_db(
                satellite_id,
                1799.0,
            ),
            35.0,
        )

        self.assertEqual(
            runtime.additional_link_loss_db(
                satellite_id,
                1800.0,
            ),
            0.0,
        )

    def test_blackout_is_active_only_in_window(
        self,
    ) -> None:
        """El blackout debe comenzar y terminar correctamente."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName.ISL_BLACKOUT
            )
        )

        satellite_id = (
            config_g3.FOLLOWER_2_ID
        )

        self.assertFalse(
            runtime.link_forced_down(
                satellite_id,
                1199.0,
            )
        )

        self.assertTrue(
            runtime.link_forced_down(
                satellite_id,
                1200.0,
            )
        )

        self.assertTrue(
            runtime.link_forced_down(
                satellite_id,
                1799.0,
            )
        )

        self.assertFalse(
            runtime.link_forced_down(
                satellite_id,
                1800.0,
            )
        )

    def test_satellite_failure_remains_active(
        self,
    ) -> None:
        """La falla permanente debe mantenerse activa."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName
                .SATELLITE_FAILURE
            )
        )

        satellite_id = (
            config_g3.FOLLOWER_2_ID
        )

        self.assertFalse(
            runtime.satellite_disabled(
                satellite_id,
                1799.0,
            )
        )

        self.assertTrue(
            runtime.satellite_disabled(
                satellite_id,
                1800.0,
            )
        )

        self.assertTrue(
            runtime.satellite_disabled(
                satellite_id,
                3600.0,
            )
        )

    def test_federated_exclusion_respects_window(
        self,
    ) -> None:
        """La exclusión FedAvg debe ser temporal."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName
                .FEDERATED_EXCLUSION
            )
        )

        satellite_id = (
            config_g3.FOLLOWER_1_ID
        )

        self.assertFalse(
            runtime.federated_excluded(
                satellite_id,
                599.0,
            )
        )

        self.assertTrue(
            runtime.federated_excluded(
                satellite_id,
                600.0,
            )
        )

        self.assertTrue(
            runtime.federated_excluded(
                satellite_id,
                2399.0,
            )
        )

        self.assertFalse(
            runtime.federated_excluded(
                satellite_id,
                2400.0,
            )
        )

    def test_update_emits_start_and_finish_events(
        self,
    ) -> None:
        """Debe registrarse el inicio y el final."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName.ISL_BLACKOUT
            )
        )

        states = self.make_states()
        energy = self.make_energy()

        start_events = runtime.update(
            time_s=1200.0,
            relative_states=states,
            energy_systems=energy,
        )

        repeated_start = runtime.update(
            time_s=1260.0,
            relative_states=states,
            energy_systems=energy,
        )

        finish_events = runtime.update(
            time_s=1800.0,
            relative_states=states,
            energy_systems=energy,
        )

        self.assertEqual(
            len(start_events),
            1,
        )

        self.assertEqual(
            start_events[0][
                "transition"
            ],
            "INICIO",
        )

        self.assertEqual(
            repeated_start,
            [],
        )

        self.assertEqual(
            len(finish_events),
            1,
        )

        self.assertEqual(
            finish_events[0][
                "transition"
            ],
            "FIN",
        )

    def test_nominal_runtime_has_no_effects(
        self,
    ) -> None:
        """El escenario nominal no altera el sistema."""

        runtime = ScenarioRuntime(
            get_scenario(
                ScenarioName.NOMINAL
            )
        )

        states = self.make_states()
        energy = self.make_energy()

        emitted = runtime.update(
            time_s=1800.0,
            relative_states=states,
            energy_systems=energy,
        )

        self.assertEqual(
            emitted,
            [],
        )

        self.assertEqual(
            runtime.active_effects(
                config_g3.FOLLOWER_1_ID,
                1800.0,
            ),
            tuple(),
        )


if __name__ == "__main__":
    unittest.main()