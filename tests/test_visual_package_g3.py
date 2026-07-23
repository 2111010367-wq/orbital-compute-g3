"""Pruebas del paquete visual G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orbital_compute.visual_package_g3 import (
    export_visual_package,
    scan_visual_files,
    validate_visual_package,
)


class TestVisualPackageG3(
    unittest.TestCase
):
    """Valida el cierre de la Fase 16."""

    def setUp(self) -> None:
        """Construye un paquete visual reducido."""

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.root = (
            Path(
                self.temporary_directory.name
            )
            / "graficas"
        )

        self.expected_counts = {
            "resumen_comparativo": 3,
            "comparacion_avanzada": 3,
        }

        for section in self.expected_counts:
            directory = (
                self.root
                / section
            )

            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            for extension in (
                "png",
                "svg",
                "pdf",
            ):
                path = (
                    directory
                    / f"figura.{extension}"
                )

                path.write_bytes(
                    b"contenido"
                )

    def tearDown(self) -> None:
        """Elimina el entorno temporal."""

        self.temporary_directory.cleanup()

    def test_six_files_are_scanned(
        self,
    ) -> None:
        """Debe detectar los seis archivos."""

        records = scan_visual_files(
            self.root
        )

        self.assertEqual(
            len(records),
            6,
        )

    def test_valid_package_is_accepted(
        self,
    ) -> None:
        """El paquete completo debe ser válido."""

        report = validate_visual_package(
            root_directory=self.root,
            expected_counts=(
                self.expected_counts
            ),
        )

        self.assertTrue(
            report.valid
        )

        self.assertEqual(
            report.total_files,
            6,
        )

    def test_missing_section_is_detected(
        self,
    ) -> None:
        """Una sección ausente debe detectarse."""

        expected = {
            **self.expected_counts,
            "series_temporales": 3,
        }

        report = validate_visual_package(
            root_directory=self.root,
            expected_counts=expected,
        )

        self.assertFalse(
            report.valid
        )

    def test_empty_file_is_detected(
        self,
    ) -> None:
        """Los archivos vacíos deben rechazarse."""

        empty_path = (
            self.root
            / "resumen_comparativo"
            / "figura.png"
        )

        empty_path.write_bytes(
            b""
        )

        report = validate_visual_package(
            root_directory=self.root,
            expected_counts=(
                self.expected_counts
            ),
        )

        self.assertFalse(
            report.valid
        )

    def test_unsupported_format_is_detected(
        self,
    ) -> None:
        """No debe aceptarse una extensión extraña."""

        invalid_path = (
            self.root
            / "resumen_comparativo"
            / "archivo.txt"
        )

        invalid_path.write_text(
            "incorrecto",
            encoding="utf-8",
        )

        report = validate_visual_package(
            root_directory=self.root,
            expected_counts={
                "resumen_comparativo": 4,
                "comparacion_avanzada": 3,
            },
        )

        self.assertFalse(
            report.valid
        )

    def test_manifest_and_inventory_exist(
        self,
    ) -> None:
        """Debe exportarse JSON y CSV."""

        output = (
            self.root.parent
            / "package"
        )

        files = export_visual_package(
            root_directory=self.root,
            output_directory=output,
            expected_counts=(
                self.expected_counts
            ),
        )

        self.assertTrue(
            files["json"].exists()
        )

        self.assertTrue(
            files["csv"].exists()
        )

    def test_manifest_reports_valid_package(
        self,
    ) -> None:
        """El manifiesto debe registrar validación."""

        output = (
            self.root.parent
            / "package"
        )

        files = export_visual_package(
            root_directory=self.root,
            output_directory=output,
            expected_counts=(
                self.expected_counts
            ),
        )

        payload = json.loads(
            files["json"].read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["report"]["valid"]
        )

        self.assertEqual(
            len(payload["files"]),
            6,
        )


if __name__ == "__main__":
    unittest.main()