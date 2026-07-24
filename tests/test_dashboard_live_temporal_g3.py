"""Pruebas de las gráficas temporales animadas del G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.callbacks import (
    build_live_temporal_figures,
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
    """Construye tres instantes temporales."""

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
                    "velocity_m_s": [
                        0.0,
                        0.01,
                        0.0,
                    ],
                    "formation_error_m": (
                        20.0
                        - time_s / 10.0
                        + index
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
                    "link_available": (
                        time_s < 120.0
                        or satellite_id
                        != "SAT-002"
                    ),
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


def trajectory_lengths(
    figure: Any,
) -> list[int]:
    """Obtiene la longitud de las curvas satelitales."""

    return [
        len(trace.x)
        for trace in figure.data
        if str(trace.name).startswith(
            "SAT-"
        )
    ]


class TestDashboardLiveTemporalG3(
    unittest.TestCase
):
    """Valida las curvas sincronizadas."""

    def setUp(self) -> None:
        """Prepara el dataset."""

        self.dataset = build_dataset()

    def test_four_figures_are_created(
        self,
    ) -> None:
        """Deben construirse cuatro figuras."""

        figures = build_live_temporal_figures(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=0.0,
        )

        self.assertEqual(
            len(figures),
            4,
        )

    def test_initial_graph_has_one_point(
        self,
    ) -> None:
        """En t=0 cada satélite tiene un punto."""

        formation, _, _, _ = (
            build_live_temporal_figures(
                dataset=self.dataset,
                scenario_name="NOMINAL",
                target_time_s=0.0,
            )
        )

        self.assertEqual(
            trajectory_lengths(
                formation
            ),
            [1, 1, 1],
        )

    def test_sixty_seconds_has_two_points(
        self,
    ) -> None:
        """En t=60 cada curva tiene dos puntos."""

        formation, _, _, _ = (
            build_live_temporal_figures(
                dataset=self.dataset,
                scenario_name="NOMINAL",
                target_time_s=60.0,
            )
        )

        self.assertEqual(
            trajectory_lengths(
                formation
            ),
            [2, 2, 2],
        )

    def test_final_time_has_three_points(
        self,
    ) -> None:
        """En t=120 deben mostrarse todos los puntos."""

        formation, soc, margin, availability = (
            build_live_temporal_figures(
                dataset=self.dataset,
                scenario_name="NOMINAL",
                target_time_s=120.0,
            )
        )

        for figure in (
            formation,
            soc,
            margin,
            availability,
        ):
            self.assertEqual(
                trajectory_lengths(
                    figure
                ),
                [3, 3, 3],
            )

    def test_title_contains_scenario(
        self,
    ) -> None:
        """Los títulos deben identificar el escenario."""

        formation, _, _, _ = (
            build_live_temporal_figures(
                dataset=self.dataset,
                scenario_name=(
                    "ISL_BLACKOUT"
                ),
                target_time_s=60.0,
            )
        )

        self.assertIn(
            "ISL_BLACKOUT",
            formation.layout.title.text,
        )

    def test_graphs_have_single_callback_owner(
        self,
    ) -> None:
        """Cada gráfica debe ser controlada una sola vez."""

        app = create_app(
            dataset=self.dataset
        )

        output_ids = (
            "graph-formation-error.figure",
            "graph-soc.figure",
            "graph-link-margin.figure",
            "graph-isl-availability.figure",
        )

        for output_id in output_ids:
            matching = [
                callback_key
                for callback_key
                in app.callback_map
                if output_id
                in callback_key
            ]

            self.assertEqual(
                len(matching),
                1,
            )


if __name__ == "__main__":
    unittest.main()