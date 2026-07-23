"""Pruebas de visualización y exportación G3."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from orbital_compute.visualization_results_g3 import (
    EXPORT_FORMATS,
    generate_phase16_summary_charts,
    load_assessment_rows,
    load_comparison_rows,
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


class TestVisualizationResultsG3(
    unittest.TestCase
):
    """Valida la infraestructura gráfica."""

    def setUp(self) -> None:
        """Crea archivos temporales de prueba."""

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

            writer.writerow(
                {
                    "scenario": "NOMINAL",
                    "maximum_final_error_m": 0.057,
                    "minimum_soc_percent": 25.0,
                    "minimum_margin_db": 40.14,
                    "link_availability_percent": 100.0,
                    "node_availability_percent": 100.0,
                    "federated_completion_percent": 71.43,
                    "final_accuracy_percent": 96.67,
                }
            )

            writer.writerow(
                {
                    "scenario": "SATELLITE_FAILURE",
                    "maximum_final_error_m": 0.835,
                    "minimum_soc_percent": 25.0,
                    "minimum_margin_db": 40.14,
                    "link_availability_percent": 66.12,
                    "node_availability_percent": 83.06,
                    "federated_completion_percent": 14.29,
                    "final_accuracy_percent": 96.67,
                }
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

            writer.writerow(
                {
                    "scenario": "NOMINAL",
                    "score": 100.0,
                    "level": "ROBUSTO",
                }
            )

            writer.writerow(
                {
                    "scenario": "SATELLITE_FAILURE",
                    "score": 69.67,
                    "level": "CRITICO",
                }
            )

        self.output_directory = (
            self.directory
            / "charts"
        )

    def tearDown(self) -> None:
        """Elimina los archivos temporales."""

        self.temporary_directory.cleanup()

    def test_comparison_rows_are_loaded(
        self,
    ) -> None:
        """Debe cargar los datos comparativos."""

        rows = load_comparison_rows(
            self.comparison_path
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertAlmostEqual(
            rows[1][
                "maximum_final_error_m"
            ],
            0.835,
        )

    def test_assessment_rows_are_loaded(
        self,
    ) -> None:
        """Debe cargar las evaluaciones."""

        rows = load_assessment_rows(
            self.assessment_path
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[1]["level"],
            "CRITICO",
        )

    def test_missing_csv_is_rejected(
        self,
    ) -> None:
        """Un archivo inexistente debe rechazarse."""

        with self.assertRaises(
            FileNotFoundError
        ):
            load_comparison_rows(
                self.directory
                / "missing.csv"
            )

    def test_four_charts_are_generated(
        self,
    ) -> None:
        """Deben producirse cuatro gráficas."""

        charts = (
            generate_phase16_summary_charts(
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
        )

        self.assertEqual(
            len(charts),
            4,
        )

    def test_each_chart_has_three_formats(
        self,
    ) -> None:
        """Cada gráfica debe exportarse tres veces."""

        charts = (
            generate_phase16_summary_charts(
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
        )

        for files in charts.values():
            self.assertEqual(
                set(files),
                set(EXPORT_FORMATS),
            )

    def test_generated_files_exist(
        self,
    ) -> None:
        """Los archivos generados deben existir."""

        charts = (
            generate_phase16_summary_charts(
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
        )

        for files in charts.values():
            for path in files.values():
                self.assertTrue(
                    path.exists()
                )

                self.assertGreater(
                    path.stat().st_size,
                    0,
                )

    def test_expected_number_of_files(
        self,
    ) -> None:
        """Deben generarse doce archivos."""

        generate_phase16_summary_charts(
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

        generated_files = [
            path
            for path
            in self.output_directory.iterdir()
            if path.is_file()
        ]

        self.assertEqual(
            len(generated_files),
            12,
        )


if __name__ == "__main__":
    unittest.main()