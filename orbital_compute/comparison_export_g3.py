"""
Exportación de la comparación de escenarios G3.

Genera archivos CSV y JSON con las métricas comparativas
obtenidas durante la Fase 15.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


COMPARISON_FIELDNAMES = (
    "scenario",
    "maximum_final_error_m",
    "delta_error_m",
    "minimum_soc_percent",
    "delta_soc_pp",
    "minimum_margin_db",
    "delta_margin_db",
    "link_availability_percent",
    "delta_link_availability_pp",
    "node_availability_percent",
    "delta_node_availability_pp",
    "federated_completion_percent",
    "delta_federated_completion_pp",
    "final_accuracy_percent",
    "delta_accuracy_pp",
)


def validate_comparison_rows(
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Valida las filas antes de exportarlas."""

    if not rows:
        raise ValueError(
            "La comparación debe contener "
            "al menos una fila"
        )

    required_fields = set(
        COMPARISON_FIELDNAMES
    )

    scenario_names: set[str] = set()

    for index, row in enumerate(rows):
        missing_fields = (
            required_fields
            - set(row)
        )

        if missing_fields:
            raise ValueError(
                f"La fila {index} no contiene: "
                f"{sorted(missing_fields)}"
            )

        scenario = str(
            row["scenario"]
        )

        if not scenario:
            raise ValueError(
                "El nombre del escenario "
                "no puede estar vacío"
            )

        if scenario in scenario_names:
            raise ValueError(
                f"Escenario duplicado: {scenario}"
            )

        scenario_names.add(
            scenario
        )


def export_comparison_csv(
    rows: Sequence[Mapping[str, Any]],
    output_path: str | Path,
) -> Path:
    """Exporta la comparación a formato CSV."""

    validate_comparison_rows(
        rows
    )

    csv_path = Path(
        output_path
    )

    csv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with csv_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=(
                COMPARISON_FIELDNAMES
            ),
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row[field]
                    for field
                    in COMPARISON_FIELDNAMES
                }
            )

    return csv_path


def export_comparison_json(
    rows: Sequence[Mapping[str, Any]],
    output_path: str | Path,
) -> Path:
    """Exporta la comparación a formato JSON."""

    validate_comparison_rows(
        rows
    )

    json_path = Path(
        output_path
    )

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": "1.0",
        "project": (
            "Arquitectura Cognitiva "
            "de Control Distribuido G3"
        ),
        "reference_scenario": "NOMINAL",
        "scenario_count": len(rows),
        "comparison": [
            {
                field: row[field]
                for field
                in COMPARISON_FIELDNAMES
            }
            for row in rows
        ],
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return json_path


def export_comparison_bundle(
    rows: Sequence[Mapping[str, Any]],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera simultáneamente CSV y JSON."""

    directory = Path(
        output_directory
    )

    csv_path = export_comparison_csv(
        rows=rows,
        output_path=(
            directory
            / "comparacion_escenarios.csv"
        ),
    )

    json_path = export_comparison_json(
        rows=rows,
        output_path=(
            directory
            / "comparacion_escenarios.json"
        ),
    )

    return {
        "csv": csv_path,
        "json": json_path,
    }


def load_exported_comparison(
    path: str | Path,
) -> dict[str, Any]:
    """Carga una comparación JSON exportada."""

    json_path = Path(
        path
    )

    if not json_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {json_path}"
        )

    payload = json.loads(
        json_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "El contenido exportado "
            "debe ser un diccionario"
        )

    return payload