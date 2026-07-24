"""
Carga y validación de datos para el dashboard profesional G3.

Este módulo no modifica el simulador. Únicamente conecta
los resultados existentes de las fases 15 y 16 con la
interfaz interactiva de la Fase 17.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCENARIO_ORDER = (
    "NOMINAL",
    "LOW_POWER",
    "ISL_DEGRADATION",
    "ISL_BLACKOUT",
    "SATELLITE_FAILURE",
    "FORMATION_DISTURBANCE",
    "FEDERATED_EXCLUSION",
    "COMBINED_FAILURE",
)


SCENARIO_FILES = {
    scenario: f"{scenario.lower()}.json"
    for scenario in SCENARIO_ORDER
}


class DashboardDataError(RuntimeError):
    """Error relacionado con los datos del dashboard."""


def normalize_scenario_name(
    scenario: object,
) -> str:
    """Normaliza el nombre de un escenario."""

    normalized = str(scenario).strip().upper()

    if not normalized:
        raise DashboardDataError(
            "El nombre del escenario está vacío."
        )

    return normalized


def read_json_file(
    file_path: str | Path,
) -> Any:
    """Lee un archivo JSON con validación de errores."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo JSON: {path}"
        )

    if not path.is_file():
        raise DashboardDataError(
            f"La ruta no corresponde a un archivo: {path}"
        )

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise DashboardDataError(
            f"JSON inválido en {path}: {error}"
        ) from error


def validate_scenario_result(
    payload: Any,
    scenario_name: str,
) -> dict[str, Any]:
    """Valida las secciones mínimas de una simulación."""

    if not isinstance(payload, Mapping):
        raise DashboardDataError(
            f"{scenario_name}: el resultado debe "
            "ser un objeto JSON."
        )

    required_sections = {
        "snapshots": list,
        "events": list,
        "federated_rounds": list,
        "summary": Mapping,
    }

    for section, expected_type in (
        required_sections.items()
    ):
        if section not in payload:
            raise DashboardDataError(
                f"{scenario_name}: falta la sección "
                f"'{section}'."
            )

        if not isinstance(
            payload[section],
            expected_type,
        ):
            raise DashboardDataError(
                f"{scenario_name}: la sección "
                f"'{section}' tiene un formato inválido."
            )

    result = dict(payload)
    result["snapshots"] = list(
        payload["snapshots"]
    )
    result["events"] = list(
        payload["events"]
    )
    result["federated_rounds"] = list(
        payload["federated_rounds"]
    )

    summary = dict(
        payload["summary"]
    )

    summary.setdefault(
        "scenario",
        scenario_name,
    )

    result["summary"] = summary

    return result


def load_scenario_result(
    file_path: str | Path,
    scenario_name: str | None = None,
) -> dict[str, Any]:
    """Carga y valida el resultado de un escenario."""

    path = Path(file_path)

    normalized_name = normalize_scenario_name(
        scenario_name
        if scenario_name is not None
        else path.stem
    )

    payload = read_json_file(
        path
    )

    return validate_scenario_result(
        payload=payload,
        scenario_name=normalized_name,
    )


def load_all_scenarios(
    scenarios_directory: str | Path,
) -> dict[str, dict[str, Any]]:
    """Carga los ocho escenarios de la campaña G3."""

    directory = Path(
        scenarios_directory
    )

    if not directory.exists():
        raise FileNotFoundError(
            "No existe el directorio de escenarios: "
            f"{directory}"
        )

    missing_files: list[str] = []

    for scenario in SCENARIO_ORDER:
        expected_path = (
            directory
            / SCENARIO_FILES[scenario]
        )

        if not expected_path.exists():
            missing_files.append(
                expected_path.name
            )

    if missing_files:
        raise FileNotFoundError(
            "Faltan archivos de escenarios: "
            + ", ".join(missing_files)
        )

    return {
        scenario: load_scenario_result(
            file_path=(
                directory
                / SCENARIO_FILES[scenario]
            ),
            scenario_name=scenario,
        )
        for scenario in SCENARIO_ORDER
    }


def extract_rows(
    payload: Any,
    candidate_keys: Sequence[str],
    document_name: str,
) -> list[dict[str, Any]]:
    """
    Extrae filas de documentos JSON con diferentes
    estructuras de exportación.
    """

    if isinstance(payload, list):
        raw_rows = payload

    elif isinstance(payload, Mapping):
        raw_rows = None

        for key in candidate_keys:
            value = payload.get(
                key
            )

            if isinstance(value, list):
                raw_rows = value
                break

        if raw_rows is None:
            mapped_rows: list[dict[str, Any]] = []

            for scenario, value in (
                payload.items()
            ):
                if not isinstance(
                    value,
                    Mapping,
                ):
                    mapped_rows = []
                    break

                row = dict(value)
                row.setdefault(
                    "scenario",
                    scenario,
                )

                mapped_rows.append(
                    row
                )

            if mapped_rows:
                raw_rows = mapped_rows

        if raw_rows is None:
            raise DashboardDataError(
                f"No se encontraron filas en "
                f"{document_name}."
            )

    else:
        raise DashboardDataError(
            f"{document_name} tiene una "
            "estructura JSON inválida."
        )

    rows: list[dict[str, Any]] = []

    for index, raw_row in enumerate(
        raw_rows
    ):
        if not isinstance(
            raw_row,
            Mapping,
        ):
            raise DashboardDataError(
                f"{document_name}: la fila "
                f"{index} no es un objeto."
            )

        row = dict(
            raw_row
        )

        if "scenario" not in row:
            raise DashboardDataError(
                f"{document_name}: la fila "
                f"{index} no contiene 'scenario'."
            )

        row["scenario"] = (
            normalize_scenario_name(
                row["scenario"]
            )
        )

        rows.append(
            row
        )

    return rows


def index_rows_by_scenario(
    rows: Sequence[Mapping[str, Any]],
    document_name: str,
) -> dict[str, dict[str, Any]]:
    """Indexa las filas utilizando el escenario."""

    indexed: dict[
        str,
        dict[str, Any],
    ] = {}

    for row in rows:
        scenario = normalize_scenario_name(
            row["scenario"]
        )

        if scenario in indexed:
            raise DashboardDataError(
                f"{document_name}: escenario "
                f"duplicado '{scenario}'."
            )

        indexed[scenario] = dict(
            row
        )

    return indexed


def load_comparison_results(
    file_path: str | Path,
) -> dict[str, dict[str, Any]]:
    """Carga la comparación de escenarios."""

    payload = read_json_file(
        file_path
    )

    rows = extract_rows(
        payload=payload,
        candidate_keys=(
            "rows",
            "comparison",
            "comparisons",
            "scenarios",
            "results",
            "data",
        ),
        document_name=(
            "comparación de escenarios"
        ),
    )

    return index_rows_by_scenario(
        rows=rows,
        document_name=(
            "comparación de escenarios"
        ),
    )


def load_resilience_assessment(
    file_path: str | Path,
) -> dict[str, dict[str, Any]]:
    """Carga la evaluación de resiliencia."""

    payload = read_json_file(
        file_path
    )

    rows = extract_rows(
        payload=payload,
        candidate_keys=(
            "rows",
            "assessment",
            "assessments",
            "evaluation",
            "evaluations",
            "ranking",
            "results",
            "scenarios",
            "data",
        ),
        document_name=(
            "evaluación de resiliencia"
        ),
    )

    return index_rows_by_scenario(
        rows=rows,
        document_name=(
            "evaluación de resiliencia"
        ),
    )


def snapshot_time_seconds(
    snapshot: Mapping[str, Any],
) -> float | None:
    """Obtiene el tiempo desde un snapshot."""

    candidate_keys = (
        "time_s",
        "simulation_time_s",
        "elapsed_time_s",
        "timestamp_s",
        "time",
    )

    for key in candidate_keys:
        if key not in snapshot:
            continue

        try:
            return float(
                snapshot[key]
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def build_scenario_summary(
    scenario_name: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Construye el resumen requerido por la interfaz."""

    snapshots = list(
        result["snapshots"]
    )

    events = list(
        result["events"]
    )

    federated_rounds = list(
        result["federated_rounds"]
    )

    satellite_ids = sorted(
        {
            str(
                snapshot["satellite_id"]
            )
            for snapshot in snapshots
            if isinstance(
                snapshot,
                Mapping,
            )
            and "satellite_id" in snapshot
        }
    )

    times = [
        time_value
        for snapshot in snapshots
        if isinstance(
            snapshot,
            Mapping,
        )
        for time_value in [
            snapshot_time_seconds(
                snapshot
            )
        ]
        if time_value is not None
    ]

    duration_s = (
        max(times)
        if times
        else 0.0
    )

    return {
        "scenario": scenario_name,
        "snapshot_count": len(
            snapshots
        ),
        "event_count": len(
            events
        ),
        "federated_round_count": len(
            federated_rounds
        ),
        "satellite_count": len(
            satellite_ids
        ),
        "satellite_ids": satellite_ids,
        "duration_s": duration_s,
        "duration_min": (
            duration_s / 60.0
        ),
    }


def validate_campaign_references(
    scenarios: Mapping[str, Any],
    comparison: Mapping[str, Any],
    assessment: Mapping[str, Any],
) -> None:
    """Comprueba la coherencia entre los documentos."""

    required = set(
        SCENARIO_ORDER
    )

    scenario_names = set(
        scenarios
    )

    comparison_names = set(
        comparison
    )

    assessment_names = set(
        assessment
    )

    if scenario_names != required:
        raise DashboardDataError(
            "La campaña no contiene exactamente "
            "los ocho escenarios requeridos."
        )

    missing_comparison = (
        required
        - comparison_names
    )

    if missing_comparison:
        raise DashboardDataError(
            "Faltan escenarios en la comparación: "
            + ", ".join(
                sorted(
                    missing_comparison
                )
            )
        )

    missing_assessment = (
        required
        - assessment_names
    )

    if missing_assessment:
        raise DashboardDataError(
            "Faltan escenarios en la evaluación: "
            + ", ".join(
                sorted(
                    missing_assessment
                )
            )
        )


def build_dashboard_dataset(
    scenarios_directory: str | Path,
    comparison_json_path: str | Path,
    assessment_json_path: str | Path,
) -> dict[str, Any]:
    """Construye el conjunto completo del dashboard."""

    scenarios = load_all_scenarios(
        scenarios_directory
    )

    comparison = load_comparison_results(
        comparison_json_path
    )

    assessment = load_resilience_assessment(
        assessment_json_path
    )

    validate_campaign_references(
        scenarios=scenarios,
        comparison=comparison,
        assessment=assessment,
    )

    scenario_summaries = {
        scenario: build_scenario_summary(
            scenario_name=scenario,
            result=scenarios[scenario],
        )
        for scenario in SCENARIO_ORDER
    }

    return {
        "schema_version": "1.0",
        "phase": "17.1.2",
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "scenario_order": list(
            SCENARIO_ORDER
        ),
        "scenario_count": len(
            SCENARIO_ORDER
        ),
        "scenarios": scenarios,
        "scenario_summaries": (
            scenario_summaries
        ),
        "comparison": comparison,
        "assessment": assessment,
    }