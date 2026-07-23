"""Pruebas de las métricas de resiliencia G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orbital_compute.resilience_metrics_g3 import (
    compare_against_nominal,
    extract_scenario_metrics,
    metrics_from_file,
)


def make_result(
    scenario: str = "NOMINAL",
    unavailable_count: int = 0,
    disabled_count: int = 0,
    completed_rounds: int = 5,
    cancelled_rounds: int = 2,
    minimum_soc: float = 0.25,
    minimum_margin_db: float = 40.14,
    maximum_error_m: float = 0.057,
    final_accuracy: float = 0.9667,
) -> dict:
    """Construye un resultado sintético."""

    return {
        "snapshots": [
            {
                "time_s": float(index),
            }
            for index in range(100)
        ],
        "events": [],
        "federated_rounds": [],
        "summary": {
            "scenario": scenario,
            "event_count": 17,
            "minimum_soc": minimum_soc,
            "minimum_link_margin_db": (
                minimum_margin_db
            ),
            "link_unavailable_snapshot_count": (
                unavailable_count
            ),
            "disabled_satellite_snapshot_count": (
                disabled_count
            ),
            "federated_rounds_completed": (
                completed_rounds
            ),
            "federated_rounds_cancelled": (
                cancelled_rounds
            ),
            "final_global_accuracy": (
                final_accuracy
            ),
            "final_formation_errors_m": {
                "SAT-000": 0.0,
                "SAT-001": maximum_error_m,
                "SAT-002": 0.010,
            },
        },
    }


class TestResilienceMetricsG3(
    unittest.TestCase
):
    """Valida las métricas comparativas."""

    def test_metrics_are_extracted(
        self,
    ) -> None:
        """Debe obtener los indicadores principales."""

        metrics = extract_scenario_metrics(
            make_result()
        )

        self.assertEqual(
            metrics.scenario,
            "NOMINAL",
        )

        self.assertEqual(
            metrics.snapshot_count,
            100,
        )

        self.assertAlmostEqual(
            metrics
            .maximum_final_formation_error_m,
            0.057,
        )

        self.assertAlmostEqual(
            metrics.minimum_soc,
            0.25,
        )

    def test_link_availability_is_calculated(
        self,
    ) -> None:
        """La disponibilidad depende de enlaces caídos."""

        metrics = extract_scenario_metrics(
            make_result(
                unavailable_count=20
            )
        )

        self.assertAlmostEqual(
            metrics.link_snapshot_availability,
            0.80,
        )

    def test_node_availability_is_calculated(
        self,
    ) -> None:
        """La disponibilidad de nodos debe calcularse."""

        metrics = extract_scenario_metrics(
            make_result(
                disabled_count=25
            )
        )

        self.assertAlmostEqual(
            metrics.node_snapshot_availability,
            0.75,
        )

    def test_federated_completion_rate(
        self,
    ) -> None:
        """Debe calcularse la tasa de rondas completadas."""

        metrics = extract_scenario_metrics(
            make_result(
                completed_rounds=4,
                cancelled_rounds=3,
            )
        )

        self.assertAlmostEqual(
            metrics.federated_completion_rate,
            4.0 / 7.0,
        )

    def test_nominal_comparison_has_zero_deltas(
        self,
    ) -> None:
        """Nominal comparado consigo mismo da cero."""

        nominal = extract_scenario_metrics(
            make_result()
        )

        comparison = (
            compare_against_nominal(
                nominal,
                nominal,
            )
        )

        for key, value in comparison.items():
            if key == "scenario":
                continue

            self.assertAlmostEqual(
                value,
                0.0,
            )

    def test_failure_comparison_detects_degradation(
        self,
    ) -> None:
        """Una falla debe producir deltas negativos."""

        nominal = extract_scenario_metrics(
            make_result()
        )

        failure = extract_scenario_metrics(
            make_result(
                scenario="ISL_BLACKOUT",
                unavailable_count=20,
                completed_rounds=4,
                cancelled_rounds=3,
            )
        )

        comparison = (
            compare_against_nominal(
                failure,
                nominal,
            )
        )

        self.assertLess(
            comparison[
                "delta_link_availability_percentage_points"
            ],
            0.0,
        )

        self.assertLess(
            comparison[
                "delta_federated_completion_percentage_points"
            ],
            0.0,
        )

    def test_metrics_can_be_loaded_from_json(
        self,
    ) -> None:
        """Las métricas deben obtenerse desde archivo."""

        with tempfile.TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "nominal.json"
            )

            path.write_text(
                json.dumps(
                    make_result()
                ),
                encoding="utf-8",
            )

            metrics = metrics_from_file(
                path
            )

            self.assertEqual(
                metrics.scenario,
                "NOMINAL",
            )

            self.assertEqual(
                metrics.snapshot_count,
                100,
            )

    def test_missing_summary_is_rejected(
        self,
    ) -> None:
        """Un resultado incompleto debe rechazarse."""

        with self.assertRaises(
            ValueError
        ):
            extract_scenario_metrics(
                {
                    "snapshots": [
                        {}
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()