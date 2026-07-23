"""Pruebas de visualización temporal G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orbital_compute.temporal_visualization_g3 import (
    generate_temporal_charts_for_scenario,
    group_snapshots_by_satellite,
    load_scenario_result,
    scenario_event_markers,
)
from orbital_compute.visualization_results_g3 import (
    EXPORT_FORMATS,
)


def make_snapshot(
    time_s: float,
    satellite_id: str,
    formation_error_m: float,
    soc: float,
    link_margin_db: float,
    link_available: bool,
) -> dict:
    """Construye un snapshot sintético."""

    return {
        "time_s": time_s,
        "time_min": time_s / 60.0,
        "satellite_id": satellite_id,
        "formation_error_m": (
            formation_error_m
        ),
        "soc": soc,
        "link_margin_db": (
            link_margin_db
        ),
        "link_available": (
            link_available
        ),
    }


class TestTemporalVisualizationG3(
    unittest.TestCase
):
    """Valida las gráficas temporales."""

    @classmethod
    def setUpClass(cls) -> None:
        """Construye un resultado temporal."""

        cls.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        cls.directory = Path(
            cls.temporary_directory.name
        )

        cls.result_path = (
            cls.directory
            / "isl_blackout.json"
        )

        snapshots = []

        for time_s in (
            0.0,
            60.0,
            120.0,
        ):
            snapshots.extend(
                [
                    make_snapshot(
                        time_s=time_s,
                        satellite_id="SAT-000",
                        formation_error_m=0.0,
                        soc=0.80,
                        link_margin_db=40.0,
                        link_available=True,
                    ),
                    make_snapshot(
                        time_s=time_s,
                        satellite_id="SAT-001",
                        formation_error_m=(
                            0.10
                            - time_s / 2000.0
                        ),
                        soc=0.75,
                        link_margin_db=38.0,
                        link_available=True,
                    ),
                    make_snapshot(
                        time_s=time_s,
                        satellite_id="SAT-002",
                        formation_error_m=0.05,
                        soc=0.70,
                        link_margin_db=35.0,
                        link_available=(
                            time_s < 60.0
                        ),
                    ),
                ]
            )

        result = {
            "scenario": {
                "name": "ISL_BLACKOUT",
            },
            "snapshots": snapshots,
            "events": [
                {
                    "time_s": 60.0,
                    "time_min": 1.0,
                    "category": "ESCENARIO",
                    "scenario": "ISL_BLACKOUT",
                    "effect": "FORCE_LINK_DOWN",
                    "satellite_id": "SAT-002",
                    "transition": "INICIO",
                    "message": (
                        "Inicio del blackout."
                    ),
                },
                {
                    "time_s": 120.0,
                    "time_min": 2.0,
                    "category": "ESCENARIO",
                    "scenario": "ISL_BLACKOUT",
                    "effect": "FORCE_LINK_DOWN",
                    "satellite_id": "SAT-002",
                    "transition": "FIN",
                    "message": (
                        "Fin del blackout."
                    ),
                },
            ],
            "summary": {
                "scenario": "ISL_BLACKOUT",
            },
        }

        cls.result_path.write_text(
            json.dumps(
                result
            ),
            encoding="utf-8",
        )

        cls.output_directory = (
            cls.directory
            / "charts"
        )

        cls.result = load_scenario_result(
            cls.result_path
        )

        cls.charts = (
            generate_temporal_charts_for_scenario(
                result_path=(
                    cls.result_path
                ),
                output_directory=(
                    cls.output_directory
                ),
            )
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """Elimina los archivos temporales."""

        cls.temporary_directory.cleanup()

    def test_result_is_loaded(
        self,
    ) -> None:
        """El JSON debe cargarse correctamente."""

        self.assertEqual(
            self.result["summary"][
                "scenario"
            ],
            "ISL_BLACKOUT",
        )

        self.assertEqual(
            len(
                self.result["snapshots"]
            ),
            9,
        )

    def test_snapshots_are_grouped(
        self,
    ) -> None:
        """Deben obtenerse tres satélites."""

        grouped = (
            group_snapshots_by_satellite(
                self.result
            )
        )

        self.assertEqual(
            set(grouped),
            {
                "SAT-000",
                "SAT-001",
                "SAT-002",
            },
        )

        self.assertEqual(
            len(
                grouped["SAT-002"]
            ),
            3,
        )

    def test_scenario_events_are_detected(
        self,
    ) -> None:
        """Deben detectarse inicio y fin."""

        markers = (
            scenario_event_markers(
                self.result
            )
        )

        self.assertEqual(
            len(markers),
            2,
        )

        self.assertEqual(
            markers[0]["transition"],
            "INICIO",
        )

        self.assertEqual(
            markers[1]["transition"],
            "FIN",
        )

    def test_four_charts_are_generated(
        self,
    ) -> None:
        """Deben generarse cuatro gráficas."""

        self.assertEqual(
            len(self.charts),
            4,
        )

    def test_each_chart_has_three_formats(
        self,
    ) -> None:
        """Cada gráfica debe tener tres formatos."""

        for files in (
            self.charts.values()
        ):
            self.assertEqual(
                set(files),
                set(EXPORT_FORMATS),
            )

    def test_twelve_files_exist(
        self,
    ) -> None:
        """Deben existir doce archivos."""

        generated_paths = [
            path
            for files
            in self.charts.values()
            for path
            in files.values()
        ]

        self.assertEqual(
            len(generated_paths),
            12,
        )

        for path in generated_paths:
            self.assertTrue(
                path.exists()
            )

            self.assertGreater(
                path.stat().st_size,
                0,
            )

    def test_incomplete_snapshot_is_rejected(
        self,
    ) -> None:
        """Un snapshot incompleto debe rechazarse."""

        invalid_result = {
            "snapshots": [
                {
                    "time_s": 0.0,
                    "satellite_id": (
                        "SAT-000"
                    ),
                }
            ]
        }

        with self.assertRaises(
            ValueError
        ):
            group_snapshots_by_satellite(
                invalid_result
            )


if __name__ == "__main__":
    unittest.main()