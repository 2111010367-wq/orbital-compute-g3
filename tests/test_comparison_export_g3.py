"""Pruebas de exportación comparativa G3."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from orbital_compute.comparison_export_g3 import (
    COMPARISON_FIELDNAMES,
    export_comparison_bundle,
    load_exported_comparison,
    validate_comparison_rows,
)


def make_row(
    scenario: str,
    soc_percent: float = 25.0,
) -> dict:
    """Construye una fila comparativa sintética."""

    return {
        "scenario": scenario,
        "maximum_final_error_m": 0.057,
        "delta_error_m": 0.0,
        "minimum_soc_percent": soc_percent,
        "delta_soc_pp": 0.0,
        "minimum_margin_db": 40.14,
        "delta_margin_db": 0.0,
        "link_availability_percent": 100.0,
        "delta_link_availability_pp": 0.0,
        "node_availability_percent": 100.0,
        "delta_node_availability_pp": 0.0,
        "federated_completion_percent": 71.43,
        "delta_federated_completion_pp": 0.0,
        "final_accuracy_percent": 96.67,
        "delta_accuracy_pp": 0.0,
    }


class TestComparisonExportG3(
    unittest.TestCase
):
    """Valida la exportación a CSV y JSON."""

    def setUp(self) -> None:
        """Crea un directorio temporal."""

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.output_directory = Path(
            self.temporary_directory.name
        )

        self.rows = [
            make_row(
                "NOMINAL"
            ),
            make_row(
                "LOW_POWER",
                soc_percent=17.39,
            ),
        ]

    def tearDown(self) -> None:
        """Elimina los archivos temporales."""

        self.temporary_directory.cleanup()

    def test_bundle_generates_csv_and_json(
        self,
    ) -> None:
        """Deben generarse los dos formatos."""

        files = export_comparison_bundle(
            rows=self.rows,
            output_directory=(
                self.output_directory
            ),
        )

        self.assertTrue(
            files["csv"].exists()
        )

        self.assertTrue(
            files["json"].exists()
        )

    def test_csv_contains_expected_rows(
        self,
    ) -> None:
        """El CSV debe contener ambas filas."""

        files = export_comparison_bundle(
            rows=self.rows,
            output_directory=(
                self.output_directory
            ),
        )

        with files["csv"].open(
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            recovered_rows = list(
                csv.DictReader(
                    csv_file
                )
            )

        self.assertEqual(
            len(recovered_rows),
            2,
        )

        self.assertEqual(
            recovered_rows[0][
                "scenario"
            ],
            "NOMINAL",
        )

        self.assertEqual(
            recovered_rows[1][
                "scenario"
            ],
            "LOW_POWER",
        )

    def test_csv_has_expected_headers(
        self,
    ) -> None:
        """El CSV debe tener columnas normalizadas."""

        files = export_comparison_bundle(
            rows=self.rows,
            output_directory=(
                self.output_directory
            ),
        )

        with files["csv"].open(
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(
                csv_file
            )

            self.assertEqual(
                tuple(
                    reader.fieldnames
                    or ()
                ),
                COMPARISON_FIELDNAMES,
            )

    def test_json_contains_metadata(
        self,
    ) -> None:
        """El JSON debe incluir metadatos."""

        files = export_comparison_bundle(
            rows=self.rows,
            output_directory=(
                self.output_directory
            ),
        )

        payload = load_exported_comparison(
            files["json"]
        )

        self.assertEqual(
            payload["schema_version"],
            "1.0",
        )

        self.assertEqual(
            payload["reference_scenario"],
            "NOMINAL",
        )

        self.assertEqual(
            payload["scenario_count"],
            2,
        )

    def test_json_preserves_values(
        self,
    ) -> None:
        """Los valores deben conservarse."""

        files = export_comparison_bundle(
            rows=self.rows,
            output_directory=(
                self.output_directory
            ),
        )

        payload = load_exported_comparison(
            files["json"]
        )

        low_power = payload[
            "comparison"
        ][1]

        self.assertEqual(
            low_power["scenario"],
            "LOW_POWER",
        )

        self.assertAlmostEqual(
            low_power[
                "minimum_soc_percent"
            ],
            17.39,
        )

    def test_empty_comparison_is_rejected(
        self,
    ) -> None:
        """No debe aceptarse una comparación vacía."""

        with self.assertRaises(
            ValueError
        ):
            validate_comparison_rows(
                []
            )

    def test_missing_field_is_rejected(
        self,
    ) -> None:
        """Las filas incompletas deben rechazarse."""

        incomplete_row = make_row(
            "NOMINAL"
        )

        incomplete_row.pop(
            "minimum_soc_percent"
        )

        with self.assertRaises(
            ValueError
        ):
            validate_comparison_rows(
                [incomplete_row]
            )


if __name__ == "__main__":
    unittest.main()