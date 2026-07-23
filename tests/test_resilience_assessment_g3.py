"""Pruebas de evaluación de resiliencia G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orbital_compute.resilience_assessment_g3 import (
    RESILIENCE_WEIGHTS,
    ResilienceLevel,
    assess_campaign,
    assess_scenario,
    calculate_penalties,
    export_assessment_bundle,
    select_critical_scenario,
)


def make_row(
    scenario: str,
    maximum_error_m: float = 0.057,
    minimum_soc_percent: float = 25.0,
    minimum_margin_db: float = 40.14,
    link_availability_percent: float = 100.0,
    node_availability_percent: float = 100.0,
    federated_completion_percent: float = 71.43,
    final_accuracy_percent: float = 96.67,
) -> dict:
    """Crea una fila comparativa."""

    return {
        "scenario": scenario,
        "maximum_final_error_m": (
            maximum_error_m
        ),
        "minimum_soc_percent": (
            minimum_soc_percent
        ),
        "minimum_margin_db": (
            minimum_margin_db
        ),
        "link_availability_percent": (
            link_availability_percent
        ),
        "node_availability_percent": (
            node_availability_percent
        ),
        "federated_completion_percent": (
            federated_completion_percent
        ),
        "final_accuracy_percent": (
            final_accuracy_percent
        ),
    }


class TestResilienceAssessmentG3(
    unittest.TestCase
):
    """Valida la clasificación de resiliencia."""

    def setUp(self) -> None:
        """Construye escenarios de referencia."""

        self.nominal = make_row(
            "NOMINAL"
        )

        self.satellite_failure = make_row(
            "SATELLITE_FAILURE",
            maximum_error_m=0.835,
            link_availability_percent=66.12,
            node_availability_percent=83.06,
            federated_completion_percent=14.29,
        )

        self.combined_failure = make_row(
            "COMBINED_FAILURE",
            maximum_error_m=0.140,
            minimum_soc_percent=12.14,
            minimum_margin_db=6.31,
        )

    def test_weights_sum_one(
        self,
    ) -> None:
        """Los pesos deben sumar uno."""

        self.assertAlmostEqual(
            sum(
                RESILIENCE_WEIGHTS.values()
            ),
            1.0,
        )

    def test_nominal_is_robust(
        self,
    ) -> None:
        """El escenario nominal debe ser robusto."""

        assessment = assess_scenario(
            self.nominal,
            self.nominal,
        )

        self.assertAlmostEqual(
            assessment.score,
            100.0,
        )

        self.assertEqual(
            assessment.level,
            ResilienceLevel.ROBUST,
        )

    def test_low_power_is_degraded(
        self,
    ) -> None:
        """Un SOC inferior al 20 % es degradado."""

        low_power = make_row(
            "LOW_POWER",
            minimum_soc_percent=17.39,
        )

        assessment = assess_scenario(
            low_power,
            self.nominal,
        )

        self.assertEqual(
            assessment.level,
            ResilienceLevel.DEGRADED,
        )

    def test_satellite_failure_is_critical(
        self,
    ) -> None:
        """La pérdida del nodo debe ser crítica."""

        assessment = assess_scenario(
            self.satellite_failure,
            self.nominal,
        )

        self.assertEqual(
            assessment.level,
            ResilienceLevel.CRITICAL,
        )

    def test_combined_failure_is_critical(
        self,
    ) -> None:
        """La falla combinada debe ser crítica."""

        assessment = assess_scenario(
            self.combined_failure,
            self.nominal,
        )

        self.assertEqual(
            assessment.level,
            ResilienceLevel.CRITICAL,
        )

    def test_penalties_remain_bounded(
        self,
    ) -> None:
        """Las penalizaciones permanecen entre 0 y 1."""

        penalties = calculate_penalties(
            self.satellite_failure,
            self.nominal,
        )

        for value in penalties.values():
            self.assertGreaterEqual(
                value,
                0.0,
            )

            self.assertLessEqual(
                value,
                1.0,
            )

    def test_campaign_requires_nominal(
        self,
    ) -> None:
        """Una campaña sin nominal debe rechazarse."""

        with self.assertRaises(
            ValueError
        ):
            assess_campaign(
                [
                    self.satellite_failure
                ]
            )

    def test_bundle_and_critical_selection(
        self,
    ) -> None:
        """Debe exportarse y seleccionarse el peor caso."""

        assessments = assess_campaign(
            [
                self.nominal,
                self.satellite_failure,
                self.combined_failure,
            ]
        )

        critical = select_critical_scenario(
            assessments
        )

        self.assertEqual(
            critical.scenario,
            "SATELLITE_FAILURE",
        )

        with tempfile.TemporaryDirectory() as directory:
            files = export_assessment_bundle(
                assessments=assessments,
                output_directory=Path(
                    directory
                ),
            )

            self.assertTrue(
                files["csv"].exists()
            )

            self.assertTrue(
                files["json"].exists()
            )

            payload = json.loads(
                files["json"].read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                payload[
                    "critical_scenario"
                ],
                "SATELLITE_FAILURE",
            )


if __name__ == "__main__":
    unittest.main()