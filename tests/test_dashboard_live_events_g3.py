"""Pruebas de eventos cognitivos progresivos del G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.animation import (
    slice_events_until_time,
)
from dashboard_g3.app import create_app
from dashboard_g3.callbacks import (
    build_live_event_view,
)


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
    """Construye snapshots y eventos de prueba."""

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
                        time_s * 0.01,
                        0.0,
                    ],
                    "formation_error_m": (
                        index * 0.05
                    ),
                    "soc": 0.80,
                    "link_margin_db": 40.0,
                    "link_available": True,
                    "satellite_operational": True,
                }
            )

    events = [
        {
            "time_s": 0.0,
            "category": "ORBITA",
            "description": "Inicio de misión",
        },
        {
            "time_s": 60.0,
            "category": "FEDAVG",
            "description": (
                "Ronda federada completada"
            ),
        },
        {
            "time_s": 120.0,
            "category": "SUPERVISOR",
            "description": (
                "Decisión cognitiva"
            ),
        },
    ]

    return {
        "snapshots": snapshots,
        "events": events,
        "federated_rounds": [],
        "summary": {},
    }


def build_dataset() -> dict[str, Any]:
    """Construye el dataset completo."""

    result = build_result()

    return {
        "scenario_order": list(
            SCENARIOS
        ),
        "scenario_count": len(
            SCENARIOS
        ),
        "scenarios": {
            scenario: result
            for scenario in SCENARIOS
        },
        "scenario_summaries": {
            scenario: {
                "scenario": scenario,
                "satellite_count": 3,
                "satellite_ids": list(
                    SATELLITE_IDS
                ),
                "duration_s": 120.0,
                "duration_min": 2.0,
                "snapshot_count": 9,
                "event_count": 3,
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


class TestDashboardLiveEventsG3(
    unittest.TestCase
):
    """Valida los eventos y el progreso."""

    def setUp(self) -> None:
        """Prepara los datos."""

        self.result = build_result()
        self.dataset = build_dataset()

    def test_zero_time_contains_one_event(
        self,
    ) -> None:
        """En t=0 debe existir un evento."""

        events = slice_events_until_time(
            result=self.result,
            target_time_s=0.0,
        )

        self.assertEqual(
            len(events),
            1,
        )

    def test_sixty_seconds_contains_two_events(
        self,
    ) -> None:
        """En t=60 deben existir dos eventos."""

        events = slice_events_until_time(
            result=self.result,
            target_time_s=60.0,
        )

        self.assertEqual(
            len(events),
            2,
        )

    def test_final_time_contains_all_events(
        self,
    ) -> None:
        """El instante final conserva los tres."""

        events = slice_events_until_time(
            result=self.result,
            target_time_s=120.0,
        )

        self.assertEqual(
            len(events),
            3,
        )

    def test_original_events_are_not_modified(
        self,
    ) -> None:
        """El recorte no altera el resultado."""

        slice_events_until_time(
            result=self.result,
            target_time_s=0.0,
        )

        self.assertEqual(
            len(self.result["events"]),
            3,
        )

    def test_live_event_view_is_generated(
        self,
    ) -> None:
        """Debe generarse el panel progresivo."""

        view = build_live_event_view(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=60.0,
        )

        self.assertEqual(
            view["current_count"],
            2,
        )

        self.assertEqual(
            view["total_count"],
            3,
        )

        self.assertIsNotNone(
            view["event_feed"]
        )

    def test_progress_components_exist(
        self,
    ) -> None:
        """Deben existir barra y etiqueta."""

        app = create_app(
            dataset=self.dataset
        )

        progress_bar = find_component(
            app.layout,
            "mission-progress-bar",
        )

        progress_label = find_component(
            app.layout,
            "mission-progress-label",
        )

        self.assertIsNotNone(
            progress_bar
        )

        self.assertIsNotNone(
            progress_label
        )

    def test_dynamic_outputs_have_single_owner(
        self,
    ) -> None:
        """Los elementos dinámicos tienen un callback."""

        app = create_app(
            dataset=self.dataset
        )

        output_ids = (
            "event-feed.children",
            "event-count-badge.children",
            "kpi-event-count.children",
            "mission-progress-bar.style",
            "mission-progress-label.children",
        )

        for output_id in output_ids:
            matching = [
                callback_key
                for callback_key
                in app.callback_map
                if output_id in callback_key
            ]

            self.assertEqual(
                len(matching),
                1,
            )


if __name__ == "__main__":
    unittest.main()