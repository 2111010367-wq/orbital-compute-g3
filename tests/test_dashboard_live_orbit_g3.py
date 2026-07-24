"""Pruebas de la órbita 3D sincronizada con el reloj."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.callbacks import (
    build_live_orbit_figure,
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


def build_result() -> dict[str, Any]:
    """Construye tres instantes orbitales."""

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
                        time_s * 0.10
                        + index * 5.0,
                        index * 2.0,
                    ],
                    "velocity_m_s": [
                        0.0,
                        0.10,
                        0.0,
                    ],
                    "formation_error_m": (
                        index * 0.05
                    ),
                    "soc": (
                        0.90
                        - index * 0.10
                        - time_s / 10000.0
                    ),
                    "link_margin_db": (
                        42.0
                        - time_s / 100.0
                    ),
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


class TestDashboardLiveOrbitG3(
    unittest.TestCase
):
    """Valida la órbita sincronizada."""

    def setUp(self) -> None:
        """Prepara el dataset."""

        self.dataset = build_dataset()

    def test_initial_orbit_has_seven_traces(
        self,
    ) -> None:
        """El instante inicial debe mostrar la formación."""

        figure = build_live_orbit_figure(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=0.0,
        )

        self.assertEqual(
            len(figure.data),
            7,
        )

    def test_initial_trajectory_has_one_point(
        self,
    ) -> None:
        """En t=0 cada trayectoria tiene un punto."""

        figure = build_live_orbit_figure(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=0.0,
        )

        trajectories = [
            trace
            for trace in figure.data
            if str(trace.name).startswith(
                "Trayectoria"
            )
        ]

        self.assertEqual(
            len(trajectories),
            3,
        )

        for trajectory in trajectories:
            self.assertEqual(
                len(trajectory.x),
                1,
            )

    def test_sixty_second_trajectory_has_two_points(
        self,
    ) -> None:
        """En t=60 deben existir dos puntos recorridos."""

        figure = build_live_orbit_figure(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=60.0,
        )

        trajectories = [
            trace
            for trace in figure.data
            if str(trace.name).startswith(
                "Trayectoria"
            )
        ]

        for trajectory in trajectories:
            self.assertEqual(
                len(trajectory.x),
                2,
            )

    def test_final_trajectory_has_three_points(
        self,
    ) -> None:
        """El instante final debe mostrar todo el recorrido."""

        figure = build_live_orbit_figure(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=120.0,
        )

        trajectories = [
            trace
            for trace in figure.data
            if str(trace.name).startswith(
                "Trayectoria"
            )
        ]

        for trajectory in trajectories:
            self.assertEqual(
                len(trajectory.x),
                3,
            )

    def test_orbit_title_contains_scenario(
        self,
    ) -> None:
        """El título debe mostrar el escenario activo."""

        figure = build_live_orbit_figure(
            dataset=self.dataset,
            scenario_name=(
                "FORMATION_DISTURBANCE"
            ),
            target_time_s=60.0,
        )

        self.assertIn(
            "FORMATION_DISTURBANCE",
            figure.layout.title.text,
        )

    def test_orbit_has_single_callback_owner(
        self,
    ) -> None:
        """Solo el callback temporal controla la órbita."""

        app = create_app(
            dataset=self.dataset
        )

        matching_outputs = [
            callback_key
            for callback_key
            in app.callback_map
            if (
                "orbit-3d-graph.figure"
                in callback_key
            )
        ]

        self.assertEqual(
            len(matching_outputs),
            1,
        )


if __name__ == "__main__":
    unittest.main()