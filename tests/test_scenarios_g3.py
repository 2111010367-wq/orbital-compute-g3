"""Pruebas del catálogo de escenarios del proyecto G3."""

from __future__ import annotations

import unittest

from orbital_compute import config_g3
from orbital_compute.scenarios_g3 import (
    SCENARIO_CATALOG,
    ScenarioDefinition,
    ScenarioEffect,
    ScenarioEvent,
    ScenarioName,
    get_scenario,
    list_scenarios,
)


class TestScenariosG3(unittest.TestCase):
    """Valida los escenarios nominales y de falla."""

    def test_catalog_contains_all_scenarios(
        self,
    ) -> None:
        """El catálogo debe contener ocho escenarios."""

        self.assertEqual(
            set(SCENARIO_CATALOG),
            set(ScenarioName),
        )

        self.assertEqual(
            len(SCENARIO_CATALOG),
            8,
        )

    def test_nominal_scenario_has_no_events(
        self,
    ) -> None:
        """El escenario nominal no debe inyectar fallas."""

        nominal = get_scenario(
            ScenarioName.NOMINAL
        )

        self.assertTrue(
            nominal.is_nominal
        )

        self.assertEqual(
            nominal.events,
            tuple(),
        )

    def test_failure_scenarios_have_events(
        self,
    ) -> None:
        """Los escenarios de falla deben incluir eventos."""

        for scenario in list_scenarios():
            if scenario.is_nominal:
                continue

            self.assertGreater(
                len(scenario.events),
                0,
                msg=scenario.name.value,
            )

    def test_all_targets_belong_to_constellation(
        self,
    ) -> None:
        """Cada evento debe apuntar a un satélite válido."""

        for scenario in list_scenarios():
            for event in scenario.events:
                self.assertIn(
                    event.satellite_id,
                    config_g3.SATELLITE_IDS,
                )

    def test_get_scenario_accepts_string(
        self,
    ) -> None:
        """Un escenario debe poder seleccionarse por texto."""

        scenario = get_scenario(
            "ISL_BLACKOUT"
        )

        self.assertEqual(
            scenario.name,
            ScenarioName.ISL_BLACKOUT,
        )

    def test_unknown_scenario_is_rejected(
        self,
    ) -> None:
        """Los nombres desconocidos deben rechazarse."""

        with self.assertRaises(
            ValueError
        ):
            get_scenario(
                "NO_EXISTE"
            )

    def test_instantaneous_event_is_active_at_start(
        self,
    ) -> None:
        """Un evento instantáneo solo actúa al inicio."""

        event = ScenarioEvent(
            effect=ScenarioEffect.SET_SOC,
            start_time_s=60.0,
            satellite_id=(
                config_g3.FOLLOWER_2_ID
            ),
            value=0.18,
        )

        self.assertFalse(
            event.is_active(0.0)
        )

        self.assertTrue(
            event.is_active(60.0)
        )

        self.assertFalse(
            event.is_active(120.0)
        )

    def test_temporary_event_respects_time_window(
        self,
    ) -> None:
        """Una falla temporal respeta su intervalo."""

        event = ScenarioEvent(
            effect=(
                ScenarioEffect.FORCE_LINK_DOWN
            ),
            start_time_s=60.0,
            duration_s=120.0,
            satellite_id=(
                config_g3.FOLLOWER_1_ID
            ),
        )

        self.assertFalse(
            event.is_active(0.0)
        )

        self.assertTrue(
            event.is_active(60.0)
        )

        self.assertTrue(
            event.is_active(179.0)
        )

        self.assertFalse(
            event.is_active(180.0)
        )

    def test_permanent_event_remains_active(
        self,
    ) -> None:
        """Una falla permanente sigue activa."""

        event = ScenarioEvent(
            effect=(
                ScenarioEffect.DISABLE_SATELLITE
            ),
            start_time_s=60.0,
            duration_s=None,
            satellite_id=(
                config_g3.FOLLOWER_2_ID
            ),
        )

        self.assertFalse(
            event.is_active(0.0)
        )

        self.assertTrue(
            event.is_active(60.0)
        )

        self.assertTrue(
            event.is_active(3600.0)
        )

    def test_invalid_soc_is_rejected(
        self,
    ) -> None:
        """Un SOC superior a uno debe rechazarse."""

        with self.assertRaises(
            ValueError
        ):
            ScenarioEvent(
                effect=(
                    ScenarioEffect.SET_SOC
                ),
                start_time_s=60.0,
                satellite_id=(
                    config_g3.FOLLOWER_2_ID
                ),
                value=1.20,
            )

    def test_invalid_target_is_rejected(
        self,
    ) -> None:
        """Un satélite inexistente debe rechazarse."""

        with self.assertRaises(
            ValueError
        ):
            ScenarioEvent(
                effect=(
                    ScenarioEffect
                    .FORCE_LINK_DOWN
                ),
                start_time_s=60.0,
                satellite_id="SAT-999",
            )

    def test_unsorted_events_are_rejected(
        self,
    ) -> None:
        """Los eventos deben ordenarse cronológicamente."""

        later_event = ScenarioEvent(
            effect=(
                ScenarioEffect.FORCE_LINK_DOWN
            ),
            start_time_s=120.0,
            satellite_id=(
                config_g3.FOLLOWER_1_ID
            ),
        )

        earlier_event = ScenarioEvent(
            effect=(
                ScenarioEffect.FORCE_LINK_DOWN
            ),
            start_time_s=60.0,
            satellite_id=(
                config_g3.FOLLOWER_1_ID
            ),
        )

        with self.assertRaises(
            ValueError
        ):
            ScenarioDefinition(
                name=(
                    ScenarioName.ISL_BLACKOUT
                ),
                description=(
                    "Escenario de prueba."
                ),
                events=(
                    later_event,
                    earlier_event,
                ),
            )


if __name__ == "__main__":
    unittest.main()