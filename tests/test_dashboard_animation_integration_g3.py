"""Pruebas de integración temporal del dashboard G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app


SCENARIOS = (
    "NOMINAL",
    "LOW_POWER",
    "ISL_DEGRADATION",
    "ISL_BLACKOUT",
    "SATELLITE_FAILURE",
    "FORMATION_DISTURBANCE",
    "FEDERATED_EXCLUSION",
    "COMBINED_FAILURE",
)

SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)


def find_component(
    component: Any,
    component_id: str,
) -> Any | None:
    """Busca recursivamente un componente Dash."""

    if component is None:
        return None

    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(
        component,
        "children",
        None,
    )

    if children is None:
        return None

    if not isinstance(
        children,
        (list, tuple),
    ):
        children = [children]

    for child in children:
        found = find_component(
            child,
            component_id,
        )

        if found is not None:
            return found

    return None


def build_result() -> dict[str, Any]:
    """Construye un escenario temporal pequeño."""

    snapshots: list[dict[str, Any]] = []

    for time_s in (
        0.0,
        60.0,
        120.0,
    ):
        for index, satellite_id in enumerate(
            SATELLITE_IDS
        ):
            snapshots.append(
                {
                    "time_s": time_s,
                    "time_min": time_s / 60.0,
                    "satellite_id": satellite_id,
                    "position_m": [
                        index * 500.0,
                        time_s * 0.001,
                        0.0,
                    ],
                    "velocity_m_s": [
                        0.0,
                        0.001,
                        0.0,
                    ],
                    "formation_error_m": (
                        index * 0.05
                    ),
                    "soc": (
                        0.80
                        - index * 0.10
                    ),
                    "link_margin_db": 40.0,
                    "link_available": True,
                    "satellite_operational": True,
                }
            )

    return {
        "snapshots": snapshots,
        "events": [],
        "federated_rounds": [],
        "summary": {},
    }


def build_dataset() -> dict[str, Any]:
    """Construye un dataset completo."""

    result = build_result()

    scenarios = {
        scenario: result
        for scenario in SCENARIOS
    }

    return {
        "scenario_order": list(
            SCENARIOS
        ),
        "scenario_count": 8,
        "scenarios": scenarios,
        "scenario_summaries": {
            scenario: {
                "scenario": scenario,
                "satellite_count": 3,
                "satellite_ids": list(
                    SATELLITE_IDS
                ),
                "duration_s": 120.0,
                "duration_min": 2.0,
                "snapshot_count": len(
                    result["snapshots"]
                ),
                "event_count": 0,
                "federated_round_count": 0,
            }
            for scenario in SCENARIOS
        },
        "assessment": {
            scenario: {
                "scenario": scenario,
                "score": 100.0,
                "classification": "ROBUSTO",
            }
            for scenario in SCENARIOS
        },
        "comparison": {
            scenario: {
                "scenario": scenario,
            }
            for scenario in SCENARIOS
        },
    }


class TestDashboardAnimationIntegrationG3(
    unittest.TestCase
):
    """Valida componentes y callbacks temporales."""

    def setUp(self) -> None:
        """Crea la aplicación de prueba."""

        self.app = create_app(
            dataset=build_dataset()
        )

    def test_animation_store_exists(
        self,
    ) -> None:
        """Debe existir el estado temporal."""

        store = find_component(
            self.app.layout,
            "animation-state-store",
        )

        self.assertIsNotNone(store)

        self.assertEqual(
            store.data["scenario"],
            "NOMINAL",
        )

        self.assertEqual(
            store.data["time_count"],
            3,
        )

    def test_interval_starts_disabled(
        self,
    ) -> None:
        """El temporizador comienza detenido."""

        interval = find_component(
            self.app.layout,
            "dashboard-clock",
        )

        self.assertIsNotNone(interval)
        self.assertTrue(interval.disabled)

        self.assertEqual(
            interval.interval,
            1000,
        )

    def test_start_button_is_enabled(
        self,
    ) -> None:
        """El botón iniciar debe estar activo."""

        button = find_component(
            self.app.layout,
            "button-start",
        )

        self.assertIsNotNone(button)
        self.assertFalse(button.disabled)

    def test_pause_button_is_disabled(
        self,
    ) -> None:
        """Pausa comienza deshabilitado."""

        button = find_component(
            self.app.layout,
            "button-pause",
        )

        self.assertIsNotNone(button)
        self.assertTrue(button.disabled)

    def test_initial_mission_time_is_zero(
        self,
    ) -> None:
        """El reloj debe comenzar en cero."""

        clock = find_component(
            self.app.layout,
            "simulation-time",
        )

        self.assertIsNotNone(clock)

        self.assertEqual(
            clock.children,
            "T+00:00:00",
        )

    def test_animation_callback_is_registered(
        self,
    ) -> None:
        """El callback temporal debe existir."""

        callback_outputs = " ".join(
            self.app.callback_map.keys()
        )

        self.assertIn(
            "animation-state-store",
            callback_outputs,
        )

        self.assertIn(
            "dashboard-clock",
            callback_outputs,
        )

        self.assertIn(
            "simulation-time",
            callback_outputs,
        )


if __name__ == "__main__":
    unittest.main()