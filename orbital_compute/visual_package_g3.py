"""
Validación y empaquetado del conjunto visual de la Fase 16.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


SUPPORTED_FORMATS = (
    "png",
    "svg",
    "pdf",
)


DEFAULT_EXPECTED_COUNTS = {
    "resumen_comparativo": 12,
    "series_temporales": 96,
    "inteligencia_eventos": 96,
    "comparacion_avanzada": 12,
}


@dataclass(frozen=True)
class VisualPackageReport:
    """Resultado de la validación visual."""

    valid: bool
    root_directory: str
    total_files: int
    total_size_bytes: int
    section_counts: dict[str, int]
    format_counts: dict[str, int]
    issues: tuple[str, ...]

    def to_dict(self) -> dict:
        """Convierte el informe en diccionario."""

        return {
            "valid": self.valid,
            "root_directory": self.root_directory,
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "section_counts": self.section_counts,
            "format_counts": self.format_counts,
            "issues": list(self.issues),
        }


def scan_visual_files(
    root_directory: str | Path,
) -> list[dict]:
    """Escanea los archivos visuales."""

    root = Path(root_directory)

    if not root.exists():
        raise FileNotFoundError(
            f"No existe el directorio: {root}"
        )

    records: list[dict] = []

    for path in sorted(
        root.rglob("*")
    ):
        if not path.is_file():
            continue

        relative_path = path.relative_to(
            root
        )

        section = (
            relative_path.parts[0]
            if relative_path.parts
            else ""
        )

        records.append(
            {
                "section": section,
                "relative_path": (
                    relative_path.as_posix()
                ),
                "filename": path.name,
                "extension": (
                    path.suffix.lower()
                    .lstrip(".")
                ),
                "size_bytes": path.stat().st_size,
            }
        )

    return records


def validate_visual_package(
    root_directory: str | Path,
    expected_counts: Mapping[str, int] | None = None,
) -> VisualPackageReport:
    """Valida estructura, formatos y cantidades."""

    root = Path(root_directory)

    expected = dict(
        expected_counts
        or DEFAULT_EXPECTED_COUNTS
    )

    records = scan_visual_files(
        root
    )

    section_counts = {
        section: 0
        for section in expected
    }

    format_counts = {
        file_format: 0
        for file_format in SUPPORTED_FORMATS
    }

    issues: list[str] = []

    for section in expected:
        section_path = root / section

        if not section_path.exists():
            issues.append(
                "No existe la sección: "
                f"{section}"
            )

    for record in records:
        section = record["section"]
        extension = record["extension"]
        size_bytes = record["size_bytes"]

        if section in section_counts:
            section_counts[section] += 1
        else:
            issues.append(
                "Sección no reconocida: "
                f"{section}"
            )

        if extension in format_counts:
            format_counts[extension] += 1
        else:
            issues.append(
                "Formato no permitido: "
                f"{record['relative_path']}"
            )

        if size_bytes <= 0:
            issues.append(
                "Archivo vacío: "
                f"{record['relative_path']}"
            )

    for section, expected_count in (
        expected.items()
    ):
        actual_count = section_counts[
            section
        ]

        if actual_count != expected_count:
            issues.append(
                f"{section}: se esperaban "
                f"{expected_count} archivos y "
                f"se encontraron {actual_count}"
            )

        if expected_count % len(
            SUPPORTED_FORMATS
        ) == 0:
            expected_per_format = (
                expected_count
                // len(SUPPORTED_FORMATS)
            )

            section_records = [
                record
                for record in records
                if record["section"] == section
            ]

            for file_format in (
                SUPPORTED_FORMATS
            ):
                actual_per_format = sum(
                    1
                    for record
                    in section_records
                    if record["extension"]
                    == file_format
                )

                if (
                    actual_per_format
                    != expected_per_format
                ):
                    issues.append(
                        f"{section}/{file_format}: "
                        f"se esperaban "
                        f"{expected_per_format} y "
                        f"se encontraron "
                        f"{actual_per_format}"
                    )

    total_size_bytes = sum(
        int(record["size_bytes"])
        for record in records
    )

    return VisualPackageReport(
        valid=not issues,
        root_directory=str(
            root.resolve()
        ),
        total_files=len(records),
        total_size_bytes=total_size_bytes,
        section_counts=section_counts,
        format_counts=format_counts,
        issues=tuple(issues),
    )


def export_visual_package(
    root_directory: str | Path,
    output_directory: str | Path,
    expected_counts: Mapping[str, int] | None = None,
) -> dict[str, Path]:
    """Exporta manifiesto JSON e inventario CSV."""

    root = Path(root_directory)
    output = Path(output_directory)

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = scan_visual_files(
        root
    )

    report = validate_visual_package(
        root_directory=root,
        expected_counts=expected_counts,
    )

    json_path = (
        output
        / "manifest_visual_fase16.json"
    )

    csv_path = (
        output
        / "inventario_visual_fase16.csv"
    )

    payload = {
        "schema_version": "1.0",
        "phase": "16",
        "report": report.to_dict(),
        "files": records,
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    fieldnames = (
        "section",
        "relative_path",
        "filename",
        "extension",
        "size_bytes",
    )

    with csv_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(records)

    return {
        "json": json_path,
        "csv": csv_path,
    }