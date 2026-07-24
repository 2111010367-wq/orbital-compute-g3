"""Pruebas de las gráficas temporales del dashboard G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.figures.temporal import (
    build_formation_error_figure,
    build_isl_availability_figure,
    build_link_margin_figure,
    build_soc_figure,
    build_temporal_figures,
)


SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)


def build_test_result() -> dict[str, Any]:
    """Crea un resultado temporal controlado."""

    snapshots: list[dict[str, Any]] = []

    for time_s in (
        0.0,
        600.0,
        1200.0,
        1800.0,
    ):
        for index, satellite_id in enumerate(
            SATELLITE_IDS
        ):
            snapshots.append(
                {
                    "time_s": time_s,
                    "satellite_id": satellite_id,
                    "formation_error_m": (
                        10.0
                        / (
                            1.0
                            + time_s
                            / 300.0
                        )
                        + index * 0.01
                    ),
                    "soc": (
                        0.80
                        - time_s
                        / 100000.0
                        - index * 0.05
                    ),
                    "link_margin_db": (
                        35.0
                        - index * 2.0
                    ),
                    "link_available": not (
                        satellite_id == "SAT-002"
                        and time_s >= 1200.0
                    ),
                }
            )

    return {
        "snapshots": snapshots,
        "events": [],
        "federated_rounds": [],
        "summary": {},
    }


class TestDashboardTemporalGraphsG3(
    unittest.TestCase
):
    """Valida las gráficas interactivas."""

    def setUp(self) -> None:
        """Prepara un resultado de prueba."""

        self.result = build_test_result()

    def test_four_temporal_figures_are_created(
        self,
    ) -> None:
        """Deben construirse cuatro figuras."""

        figures = build_temporal_figures(
            result=self.result,
            scenario_name="NOMINAL",
        )

        self.assertEqual(
            len(figures),
            4,
        )

    def test_formation_figure_has_three_traces(
        self,
    ) -> None:
        """El error debe incluir tres satélites."""

        figure = (
            build_formation_error_figure(
                result=self.result,
                scenario_name="NOMINAL",
            )
        )

        self.assertEqual(
            len(figure.data),
            3,
        )

    def test_soc_is_expressed_as_percentage(
        self,
    ) -> None:
        """El SOC debe normalizarse a porcentaje."""

        figure = build_soc_figure(
            result=self.result,
            scenario_name="LOW_POWER",
        )

        first_value = figure.data[0].y[0]

        self.assertAlmostEqual(
            first_value,
            80.0,
        )

    def test_link_margin_has_three_traces(
        self,
    ) -> None:
        """El margen Ka debe incluir tres curvas."""

        figure = build_link_margin_figure(
            result=self.result,
            scenario_name="ISL_DEGRADATION",
        )

        self.assertEqual(
            len(figure.data),
            3,
        )

    def test_availability_contains_binary_values(
        self,
    ) -> None:
        """La disponibilidad solo admite 0 y 1."""

        figure = (
            build_isl_availability_figure(
                result=self.result,
                scenario_name="ISL_BLACKOUT",
            )
        )

        values = {
            int(value)
            for trace in figure.data
            for value in trace.y
        }

        self.assertTrue(
            values.issubset(
                {0, 1}
            )
        )

        self.assertIn(
            0,
            values,
        )

    def test_time_axis_is_converted_to_minutes(
        self,
    ) -> None:
        """Los segundos deben mostrarse en minutos."""

        figure = build_soc_figure(
            result=self.result,
            scenario_name="NOMINAL",
        )

        self.assertEqual(
            list(figure.data[0].x),
            [
                0.0,
                10.0,
                20.0,
                30.0,
            ],
        )

    def test_figures_include_scenario_name(
        self,
    ) -> None:
        """El título debe identificar el escenario."""

        figure = build_link_margin_figure(
            result=self.result,
            scenario_name="COMBINED_FAILURE",
        )

        self.assertIn(
            "COMBINED_FAILURE",
            figure.layout.title.text,
        )

    def test_dashboard_registers_graph_outputs(
        self,
    ) -> None:
        """El callback debe actualizar las gráficas."""

        scenarios = {
            scenario: self.result
            for scenario in (
                "NOMINAL",
                "LOW_POWER",
                "ISL_DEGRADATION",
                "ISL_BLACKOUT",
                "SATELLITE_FAILURE",
                "FORMATION_DISTURBANCE",
                "FEDERATED_EXCLUSION",
                "COMBINED_FAILURE",
            )
        }

        summaries = {
            scenario: {
                "scenario": scenario,
                "satellite_count": 3,
                "satellite_ids": list(
                    SATELLITE_IDS
                ),
                "duration_min": 30.0,
                "snapshot_count": len(
                    self.result["snapshots"]
                ),
                "event_count": 0,
            }
            for scenario in scenarios
        }

        assessment = {
            scenario: {
                "scenario": scenario,
                "score": 100.0,
                "classification": "ROBUSTO",
            }
            for scenario in scenarios
        }

        dataset = {
            "scenario_order": list(
                scenarios.keys()
            ),
            "scenario_count": 8,
            "scenarios": scenarios,
            "scenario_summaries": summaries,
            "assessment": assessment,
            "comparison": {
                scenario: {
                    "scenario": scenario
                }
                for scenario in scenarios
            },
        }

        app = create_app(
            dataset=dataset
        )

        callback_outputs = " ".join(
            app.callback_map.keys()
        )

        self.assertIn(
            "graph-formation-error",
            callback_outputs,
        )

        self.assertIn(
            "graph-soc",
            callback_outputs,
        )

        self.assertIn(
            "graph-link-margin",
            callback_outputs,
        )

        self.assertIn(
            "graph-isl-availability",
            callback_outputs,
        )


if __name__ == "__main__":
    unittest.main()