"""Pruebas de visualización avanzada G3."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from orbital_compute.advanced_visualization_g3 import (
    build_health_matrix,
    generate_advanced_visualizations,
    scenario_health_vector,
)
from orbital_compute.visualization_results_g3 import (
    EXPORT_FORMATS,
)


COMPARISON_HEADERS = (
    "scenario",
    "maximum_final_error_m",
    "minimum_soc_percent",
    "minimum_margin_db",
    "link_availability_percent",
    "node_availability_percent",
    "federated_completion_percent",
    "final_accuracy_percent",
)


ASSESSMENT_HEADERS = (
    "scenario",
    "score",
    "level",
)


def comparison_row(
    scenario: str,
    error_m: float,
    soc_percent: float,
    margin_db: float,
    link_percent: float,
    node_percent: float,
    federated_percent: float,
) -> dict:
    """Construye una fila de comparación."""

    return {
        "scenario": scenario,
        "maximum_final_error_m": error_m,
        "minimum_soc_percent": soc_percent,
        "minimum_margin_db": margin_db,
        "link_availability_percent": (
            link_percent
        ),
        "node_availability_percent": (
            node_percent
        ),
        "federated_completion_percent": (
            federated_percent
        ),
        "final_accuracy_percent": 96.67,
    }


class TestAdvancedVisualizationG3(
    unittest.TestCase
):
    """Valida las figuras avanzadas."""

    def setUp(self) -> None:
        """Crea archivos temporales."""

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.directory = Path(
            self.temporary_directory.name
        )

        self.comparison_path = (
            self.directory
            / "comparison.csv"
        )

        self.assessment_path = (
            self.directory
            / "assessment.csv"
        )

        self.output_directory = (
            self.directory
            / "charts"
        )

        self.rows = [
            comparison_row(
                scenario="NOMINAL",
                error_m=0.057,
                soc_percent=25.0,
                margin_db=40.14,
                link_percent=100.0,
                node_percent=100.0,
                federated_percent=71.43,
            ),
            comparison_row(
                scenario="SATELLITE_FAILURE",
                error_m=0.835,
                soc_percent=25.0,
                margin_db=40.14,
                link_percent=66.12,
                node_percent=83.06,
                federated_percent=14.29,
            ),
            comparison_row(
                scenario="COMBINED_FAILURE",
                error_m=0.140,
                soc_percent=12.14,
                margin_db=6.31,
                link_percent=100.0,
                node_percent=100.0,
                federated_percent=71.43,
            ),
        ]

        with self.comparison_path.open(
            mode="w",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=(
                    COMPARISON_HEADERS
                ),
            )

            writer.writeheader()
            writer.writerows(
                self.rows
            )

        with self.assessment_path.open(
            mode="w",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=(
                    ASSESSMENT_HEADERS
                ),
            )

            writer.writeheader()

            writer.writerows(
                [
                    {
                        "scenario": "NOMINAL",
                        "score": 100.0,
                        "level": "ROBUSTO",
                    },
                    {
                        "scenario": (
                            "SATELLITE_FAILURE"
                        ),
                        "score": 69.67,
                        "level": "CRITICO",
                    },
                    {
                        "scenario": (
                            "COMBINED_FAILURE"
                        ),
                        "score": 71.21,
                        "level": "CRITICO",
                    },
                ]
            )

    def tearDown(self) -> None:
        """Elimina el entorno temporal."""

        self.temporary_directory.cleanup()

    def test_health_matrix_has_expected_shape(
        self,
    ) -> None:
        """La matriz debe ser de tres por siete."""

        _, metrics, matrix = (
            build_health_matrix(
                self.rows
            )
        )

        self.assertEqual(
            len(metrics),
            7,
        )

        self.assertEqual(
            matrix.shape,
            (
                3,
                7,
            ),
        )

    def test_health_values_are_bounded(
        self,
    ) -> None:
        """Todos los indicadores permanecen entre 0 y 100."""

        nominal = self.rows[0]

        values = scenario_health_vector(
            row=self.rows[1],
            nominal_row=nominal,
        )

        for value in values:
            self.assertGreaterEqual(
                value,
                0.0,
            )

            self.assertLessEqual(
                value,
                100.0,
            )

    def test_failure_has_degraded_health(
        self,
    ) -> None:
        """La falla satelital debe mostrar degradación."""

        nominal = self.rows[0]

        values = scenario_health_vector(
            row=self.rows[1],
            nominal_row=nominal,
        )

        self.assertLess(
            values[0],
            100.0,
        )

        self.assertLess(
            values[3],
            100.0,
        )

        self.assertLess(
            values[5],
            100.0,
        )

    def test_four_charts_are_generated(
        self,
    ) -> None:
        """Deben generarse cuatro figuras."""

        charts = generate_advanced_visualizations(
            comparison_csv_path=(
                self.comparison_path
            ),
            assessment_csv_path=(
                self.assessment_path
            ),
            output_directory=(
                self.output_directory
            ),
        )

        self.assertEqual(
            len(charts),
            4,
        )

    def test_each_chart_has_three_formats(
        self,
    ) -> None:
        """Cada figura debe tener tres formatos."""

        charts = generate_advanced_visualizations(
            comparison_csv_path=(
                self.comparison_path
            ),
            assessment_csv_path=(
                self.assessment_path
            ),
            output_directory=(
                self.output_directory
            ),
        )

        for files in charts.values():
            self.assertEqual(
                set(files),
                set(EXPORT_FORMATS),
            )

    def test_twelve_files_are_generated(
        self,
    ) -> None:
        """Deben existir doce archivos."""

        generate_advanced_visualizations(
            comparison_csv_path=(
                self.comparison_path
            ),
            assessment_csv_path=(
                self.assessment_path
            ),
            output_directory=(
                self.output_directory
            ),
        )

        files = list(
            self.output_directory.iterdir()
        )

        self.assertEqual(
            len(files),
            12,
        )

        for path in files:
            self.assertGreater(
                path.stat().st_size,
                0,
            )

    def test_campaign_without_nominal_is_rejected(
        self,
    ) -> None:
        """La matriz necesita referencia nominal."""

        rows_without_nominal = [
            self.rows[1],
            self.rows[2],
        ]

        with self.assertRaises(
            ValueError
        ):
            build_health_matrix(
                rows_without_nominal
            )


if __name__ == "__main__":
    unittest.main()