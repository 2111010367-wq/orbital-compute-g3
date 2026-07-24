"""Pruebas del cargador de datos del dashboard G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dashboard_g3.data_loader import (
    DashboardDataError,
    SCENARIO_FILES,
    SCENARIO_ORDER,
    build_dashboard_dataset,
    load_all_scenarios,
    load_scenario_result,
)


class TestDashboardDataLoaderG3(
    unittest.TestCase
):
    """Valida la conexión con los resultados."""

    def setUp(self) -> None:
        """Construye una campaña temporal."""

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.root = Path(
            self.temporary_directory.name
        )

        self.scenarios_directory = (
            self.root
            / "escenarios"
        )

        self.scenarios_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for scenario in SCENARIO_ORDER:
            payload = {
                "snapshots": [
                    {
                        "time_s": 0.0,
                        "satellite_id": "SAT-000",
                        "soc": 0.80,
                    },
                    {
                        "time_s": 60.0,
                        "satellite_id": "SAT-001",
                        "soc": 0.70,
                    },
                    {
                        "time_s": 60.0,
                        "satellite_id": "SAT-002",
                        "soc": 0.60,
                    },
                ],
                "events": [],
                "federated_rounds": [],
                "summary": {
                    "satellite_count": 3,
                },
            }

            path = (
                self.scenarios_directory
                / SCENARIO_FILES[scenario]
            )

            path.write_text(
                json.dumps(
                    payload
                ),
                encoding="utf-8",
            )

        self.comparison_path = (
            self.root
            / "comparison.json"
        )

        self.assessment_path = (
            self.root
            / "assessment.json"
        )

        comparison_payload = {
            "metadata": {
                "scenario_count": 8,
            },
            "rows": [
                {
                    "scenario": scenario,
                    "minimum_soc_percent": 25.0,
                }
                for scenario in SCENARIO_ORDER
            ],
        }

        assessment_payload = {
            "results": [
                {
                    "scenario": scenario,
                    "score": 100.0,
                    "level": "ROBUSTO",
                }
                for scenario in SCENARIO_ORDER
            ],
        }

        self.comparison_path.write_text(
            json.dumps(
                comparison_payload
            ),
            encoding="utf-8",
        )

        self.assessment_path.write_text(
            json.dumps(
                assessment_payload
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        """Elimina los archivos temporales."""

        self.temporary_directory.cleanup()

    def build_dataset(self) -> dict:
        """Construye el dataset de prueba."""

        return build_dashboard_dataset(
            scenarios_directory=(
                self.scenarios_directory
            ),
            comparison_json_path=(
                self.comparison_path
            ),
            assessment_json_path=(
                self.assessment_path
            ),
        )

    def test_all_eight_scenarios_are_loaded(
        self,
    ) -> None:
        """Deben cargarse los ocho escenarios."""

        scenarios = load_all_scenarios(
            self.scenarios_directory
        )

        self.assertEqual(
            tuple(
                scenarios
            ),
            SCENARIO_ORDER,
        )

    def test_dataset_contains_required_sections(
        self,
    ) -> None:
        """El dataset debe contener sus bloques."""

        dataset = self.build_dataset()

        self.assertIn(
            "scenarios",
            dataset,
        )

        self.assertIn(
            "comparison",
            dataset,
        )

        self.assertIn(
            "assessment",
            dataset,
        )

        self.assertIn(
            "scenario_summaries",
            dataset,
        )

    def test_summary_detects_three_satellites(
        self,
    ) -> None:
        """El resumen debe detectar tres nodos."""

        dataset = self.build_dataset()

        summary = dataset[
            "scenario_summaries"
        ]["NOMINAL"]

        self.assertEqual(
            summary[
                "satellite_count"
            ],
            3,
        )

        self.assertEqual(
            summary[
                "satellite_ids"
            ],
            [
                "SAT-000",
                "SAT-001",
                "SAT-002",
            ],
        )

    def test_comparison_is_indexed_by_scenario(
        self,
    ) -> None:
        """La comparación debe indexarse."""

        dataset = self.build_dataset()

        self.assertIn(
            "COMBINED_FAILURE",
            dataset["comparison"],
        )

    def test_assessment_is_indexed_by_scenario(
        self,
    ) -> None:
        """La evaluación debe indexarse."""

        dataset = self.build_dataset()

        self.assertEqual(
            dataset["assessment"][
                "SATELLITE_FAILURE"
            ]["score"],
            100.0,
        )

    def test_missing_scenario_file_is_rejected(
        self,
    ) -> None:
        """Un escenario faltante debe rechazarse."""

        missing_path = (
            self.scenarios_directory
            / SCENARIO_FILES[
                "ISL_BLACKOUT"
            ]
        )

        missing_path.unlink()

        with self.assertRaises(
            FileNotFoundError
        ):
            load_all_scenarios(
                self.scenarios_directory
            )

    def test_invalid_scenario_payload_is_rejected(
        self,
    ) -> None:
        """Un resultado incompleto debe rechazarse."""

        invalid_path = (
            self.root
            / "invalid.json"
        )

        invalid_path.write_text(
            json.dumps(
                {
                    "summary": {},
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(
            DashboardDataError
        ):
            load_scenario_result(
                invalid_path,
                "NOMINAL",
            )

    def test_dataset_is_json_serializable(
        self,
    ) -> None:
        """El dataset debe enviarse al navegador."""

        dataset = self.build_dataset()

        serialized = json.dumps(
            dataset,
            ensure_ascii=False,
        )

        self.assertIn(
            "COMBINED_FAILURE",
            serialized,
        )


if __name__ == "__main__":
    unittest.main()