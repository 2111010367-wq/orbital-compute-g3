"""Pruebas de visualización de FedAvg, supervisor y eventos G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orbital_compute.intelligence_visualization_g3 import (
    cognitive_decision_counts,
    generate_intelligence_charts_for_scenario,
    load_scenario_result,
    normalize_events,
    normalize_federated_rounds,
)
from orbital_compute.visualization_results_g3 import EXPORT_FORMATS


class TestIntelligenceVisualizationG3(unittest.TestCase):
    """Valida la infraestructura gráfica de inteligencia."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crea un resultado sintético y sus figuras."""

        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temporary_directory.name)
        cls.result_path = cls.directory / "combined_failure.json"
        cls.output_directory = cls.directory / "charts"

        result = {
            "scenario": {"name": "COMBINED_FAILURE"},
            "summary": {"scenario": "COMBINED_FAILURE"},
            "snapshots": [
                {
                    "time_s": 0.0,
                    "satellite_id": "SAT-000",
                    "action": "CONTROL_FORMACION",
                },
                {
                    "time_s": 0.0,
                    "satellite_id": "SAT-001",
                    "action": "AHORRO_ENERGIA",
                },
                {
                    "time_s": 60.0,
                    "satellite_id": "SAT-000",
                    "decision": {"action": "CONTROL_FORMACION"},
                },
            ],
            "events": [
                {
                    "time_s": 600.0,
                    "category": "ESCENARIO",
                    "effect": "LOW_SOC",
                    "transition": "INICIO",
                    "satellite_id": "SAT-002",
                },
                {
                    "time_s": 1200.0,
                    "category": "FEDAVG",
                    "effect": "ROUND_COMPLETED",
                },
            ],
            "federated_rounds": [
                {
                    "round_index": 1,
                    "time_s": 0.0,
                    "status": "COMPLETADA",
                    "global_loss": 0.69,
                    "global_accuracy": 0.50,
                    "participants": [
                        "SAT-000",
                        "SAT-001",
                    ],
                    "excluded": ["SAT-002"],
                },
                {
                    "round_index": 2,
                    "time_s": 600.0,
                    "status": "CANCELADA",
                    "participants": ["SAT-000"],
                    "excluded": [
                        "SAT-001",
                        "SAT-002",
                    ],
                },
                {
                    "round_index": 3,
                    "time_s": 1200.0,
                    "completed": True,
                    "loss": 0.20,
                    "accuracy": 0.95,
                    "participant_count": 3,
                    "excluded_count": 0,
                },
            ],
        }

        cls.result_path.write_text(
            json.dumps(result),
            encoding="utf-8",
        )

        cls.result = load_scenario_result(
            cls.result_path
        )
        cls.charts = (
            generate_intelligence_charts_for_scenario(
                result_path=cls.result_path,
                output_directory=cls.output_directory,
            )
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """Elimina los archivos temporales."""

        cls.temporary_directory.cleanup()

    def test_result_is_loaded(self) -> None:
        """El JSON debe cargarse correctamente."""

        self.assertEqual(
            self.result["summary"]["scenario"],
            "COMBINED_FAILURE",
        )

    def test_federated_rounds_are_normalized(self) -> None:
        """Deben normalizarse las tres rondas."""

        rounds = normalize_federated_rounds(
            self.result
        )

        self.assertEqual(len(rounds), 3)
        self.assertEqual(
            rounds[1]["status"],
            "CANCELADA",
        )
        self.assertEqual(
            rounds[0]["participant_count"],
            2,
        )

    def test_cognitive_decisions_are_counted(self) -> None:
        """Las acciones cognitivas deben contarse."""

        counts = cognitive_decision_counts(
            self.result
        )

        self.assertEqual(
            counts["CONTROL_FORMACION"],
            2,
        )
        self.assertEqual(
            counts["AHORRO_ENERGIA"],
            1,
        )

    def test_events_are_normalized(self) -> None:
        """Los eventos deben conservar tiempo y categoría."""

        events = normalize_events(self.result)

        self.assertEqual(len(events), 2)
        self.assertAlmostEqual(
            events[0]["time_min"],
            10.0,
        )
        self.assertEqual(
            events[0]["category"],
            "ESCENARIO",
        )

    def test_four_charts_are_generated(self) -> None:
        """Deben generarse cuatro figuras."""

        self.assertEqual(len(self.charts), 4)

    def test_each_chart_has_three_formats(self) -> None:
        """Cada figura debe exportarse en tres formatos."""

        for files in self.charts.values():
            self.assertEqual(
                set(files),
                set(EXPORT_FORMATS),
            )

    def test_twelve_files_exist(self) -> None:
        """Deben existir doce archivos no vacíos."""

        paths = [
            path
            for files in self.charts.values()
            for path in files.values()
        ]

        self.assertEqual(len(paths), 12)

        for path in paths:
            self.assertTrue(path.exists())
            self.assertGreater(
                path.stat().st_size,
                0,
            )


if __name__ == "__main__":
    unittest.main()
