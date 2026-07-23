"""
Visualización temporal de escenarios del proyecto G3.

Este módulo genera gráficas de:

- Error de formación.
- Estado de carga SOC.
- Margen del enlace Ka.
- Disponibilidad ISL.

Los eventos de escenario se representan mediante
marcadores verticales sobre las gráficas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from orbital_compute.scenarios_g3 import (
    ScenarioName,
)
from orbital_compute.visualization_results_g3 import (
    save_figure_bundle,
)


REQUIRED_SNAPSHOT_FIELDS = {
    "satellite_id",
    "formation_error_m",
    "soc",
    "link_margin_db",
    "link_available",
}


def snapshot_time_min(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo del snapshot en minutos."""

    if "time_min" in snapshot:
        return float(
            snapshot["time_min"]
        )

    if "time_s" in snapshot:
        return float(
            snapshot["time_s"]
        ) / 60.0

    raise ValueError(
        "El snapshot no contiene "
        "time_min ni time_s"
    )


def event_time_min(
    event: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo del evento en minutos."""

    if "time_min" in event:
        return float(
            event["time_min"]
        )

    if "time_s" in event:
        return float(
            event["time_s"]
        ) / 60.0

    raise ValueError(
        "El evento no contiene "
        "time_min ni time_s"
    )


def load_scenario_result(
    path: str | Path,
) -> dict[str, Any]:
    """Carga un resultado JSON de la Fase 15."""

    result_path = Path(path)

    if not result_path.exists():
        raise FileNotFoundError(
            f"No existe el resultado: {result_path}"
        )

    result = json.loads(
        result_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "El resultado debe ser "
            "un diccionario JSON"
        )

    if "snapshots" not in result:
        raise ValueError(
            "El resultado no contiene snapshots"
        )

    if "events" not in result:
        raise ValueError(
            "El resultado no contiene events"
        )

    if not isinstance(
        result["snapshots"],
        list,
    ):
        raise ValueError(
            "snapshots debe ser una lista"
        )

    if not isinstance(
        result["events"],
        list,
    ):
        raise ValueError(
            "events debe ser una lista"
        )

    return result


def validate_snapshot(
    snapshot: Mapping[str, Any],
) -> None:
    """Valida los campos de un snapshot."""

    missing_fields = (
        REQUIRED_SNAPSHOT_FIELDS
        - set(snapshot)
    )

    if missing_fields:
        raise ValueError(
            "Snapshot incompleto. "
            f"Faltan: {sorted(missing_fields)}"
        )

    snapshot_time_min(
        snapshot
    )


def group_snapshots_by_satellite(
    result: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Agrupa los snapshots por satélite."""

    if "snapshots" not in result:
        raise ValueError(
            "El resultado no contiene snapshots"
        )

    snapshots = result["snapshots"]

    if not isinstance(
        snapshots,
        list,
    ):
        raise ValueError(
            "snapshots debe ser una lista"
        )

    if not snapshots:
        raise ValueError(
            "No existen snapshots para graficar"
        )

    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for snapshot in snapshots:
        if not isinstance(
            snapshot,
            Mapping,
        ):
            raise ValueError(
                "Cada snapshot debe ser "
                "un diccionario"
            )

        validate_snapshot(
            snapshot
        )

        satellite_id = str(
            snapshot["satellite_id"]
        )

        grouped.setdefault(
            satellite_id,
            [],
        ).append(
            dict(snapshot)
        )

    for satellite_snapshots in (
        grouped.values()
    ):
        satellite_snapshots.sort(
            key=snapshot_time_min
        )

    return grouped


def scenario_event_markers(
    result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Obtiene los eventos inyectados por escenarios."""

    events = result.get(
        "events",
        [],
    )

    markers: list[
        dict[str, Any]
    ] = []

    for event in events:
        if not isinstance(
            event,
            Mapping,
        ):
            continue

        if (
            event.get("category")
            != "ESCENARIO"
        ):
            continue

        markers.append(
            {
                "time_min": event_time_min(
                    event
                ),
                "effect": str(
                    event.get(
                        "effect",
                        "EVENTO",
                    )
                ),
                "transition": str(
                    event.get(
                        "transition",
                        "",
                    )
                ),
                "satellite_id": str(
                    event.get(
                        "satellite_id",
                        "",
                    )
                ),
                "message": str(
                    event.get(
                        "message",
                        "",
                    )
                ),
            }
        )

    markers.sort(
        key=lambda marker: (
            marker["time_min"]
        )
    )

    return markers


def result_scenario_name(
    result: Mapping[str, Any],
) -> str:
    """Obtiene el nombre del escenario."""

    summary = result.get(
        "summary",
        {},
    )

    if isinstance(
        summary,
        Mapping,
    ):
        scenario_name = summary.get(
            "scenario"
        )

        if scenario_name:
            return str(
                scenario_name
            )

    scenario_section = result.get(
        "scenario"
    )

    if isinstance(
        scenario_section,
        Mapping,
    ):
        scenario_name = (
            scenario_section.get(
                "name"
            )
        )

        if scenario_name:
            return str(
                scenario_name
            )

    return "ESCENARIO"


def add_event_markers(
    axis: plt.Axes,
    markers: Sequence[
        Mapping[str, Any]
    ],
) -> None:
    """Añade líneas verticales de eventos."""

    for marker in markers:
        time_min = float(
            marker["time_min"]
        )

        transition = str(
            marker.get(
                "transition",
                "",
            )
        )

        effect = str(
            marker.get(
                "effect",
                "EVENTO",
            )
        )

        satellite_id = str(
            marker.get(
                "satellite_id",
                "",
            )
        )

        axis.axvline(
            time_min,
            linestyle="--",
            linewidth=1.0,
            alpha=0.45,
        )

        label_parts = [
            effect,
            transition,
        ]

        if satellite_id:
            label_parts.append(
                satellite_id
            )

        label = " ".join(
            part
            for part in label_parts
            if part
        )

        axis.text(
            time_min,
            0.98,
            label,
            transform=(
                axis.get_xaxis_transform()
            ),
            rotation=90,
            va="top",
            ha="right",
            fontsize=7,
            alpha=0.75,
        )


def plot_formation_error_time_series(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica el error de formación temporal."""

    grouped = (
        group_snapshots_by_satellite(
            result
        )
    )

    markers = scenario_event_markers(
        result
    )

    scenario_name = (
        result_scenario_name(
            result
        )
    )

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    for (
        satellite_id,
        snapshots,
    ) in grouped.items():
        times = [
            snapshot_time_min(
                snapshot
            )
            for snapshot in snapshots
        ]

        errors = [
            float(
                snapshot[
                    "formation_error_m"
                ]
            )
            for snapshot in snapshots
        ]

        axis.plot(
            times,
            errors,
            label=satellite_id,
            linewidth=1.8,
        )

    axis.axhline(
        0.50,
        linestyle="--",
        label="Umbral degradado: 0.50 m",
    )

    axis.axhline(
        1.00,
        linestyle=":",
        label="Umbral crítico: 1.00 m",
    )

    add_event_markers(
        axis,
        markers,
    )

    axis.set_title(
        "Evolución del error de formación\n"
        f"Escenario: {scenario_name}"
    )

    axis.set_xlabel(
        "Tiempo de simulación [min]"
    )

    axis.set_ylabel(
        "Error de formación [m]"
    )

    axis.grid(
        alpha=0.30,
    )

    axis.legend(
        loc="best"
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "01_error_formacion_temporal"
        ),
    )


def plot_soc_time_series(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica la evolución temporal del SOC."""

    grouped = (
        group_snapshots_by_satellite(
            result
        )
    )

    markers = scenario_event_markers(
        result
    )

    scenario_name = (
        result_scenario_name(
            result
        )
    )

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    for (
        satellite_id,
        snapshots,
    ) in grouped.items():
        times = [
            snapshot_time_min(
                snapshot
            )
            for snapshot in snapshots
        ]

        soc_percent = [
            float(
                snapshot["soc"]
            )
            * 100.0
            for snapshot in snapshots
        ]

        axis.plot(
            times,
            soc_percent,
            label=satellite_id,
            linewidth=1.8,
        )

    axis.axhline(
        20.0,
        linestyle="--",
        label="Umbral degradado: 20 %",
    )

    axis.axhline(
        15.0,
        linestyle=":",
        label="Umbral crítico: 15 %",
    )

    add_event_markers(
        axis,
        markers,
    )

    axis.set_title(
        "Evolución del estado de carga\n"
        f"Escenario: {scenario_name}"
    )

    axis.set_xlabel(
        "Tiempo de simulación [min]"
    )

    axis.set_ylabel(
        "Estado de carga SOC [%]"
    )

    axis.set_ylim(
        0.0,
        105.0,
    )

    axis.grid(
        alpha=0.30,
    )

    axis.legend(
        loc="best"
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "02_soc_temporal"
        ),
    )


def plot_link_margin_time_series(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica la evolución del margen Ka."""

    grouped = (
        group_snapshots_by_satellite(
            result
        )
    )

    markers = scenario_event_markers(
        result
    )

    scenario_name = (
        result_scenario_name(
            result
        )
    )

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    for (
        satellite_id,
        snapshots,
    ) in grouped.items():
        times = [
            snapshot_time_min(
                snapshot
            )
            for snapshot in snapshots
        ]

        margins = [
            float(
                snapshot[
                    "link_margin_db"
                ]
            )
            for snapshot in snapshots
        ]

        axis.plot(
            times,
            margins,
            label=satellite_id,
            linewidth=1.8,
        )

    axis.axhline(
        10.0,
        linestyle="--",
        label="Margen degradado: 10 dB",
    )

    axis.axhline(
        3.0,
        linestyle=":",
        label="Margen crítico: 3 dB",
    )

    add_event_markers(
        axis,
        markers,
    )

    axis.set_title(
        "Evolución del margen del enlace Ka\n"
        f"Escenario: {scenario_name}"
    )

    axis.set_xlabel(
        "Tiempo de simulación [min]"
    )

    axis.set_ylabel(
        "Margen del enlace [dB]"
    )

    axis.grid(
        alpha=0.30,
    )

    axis.legend(
        loc="best"
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "03_margen_ka_temporal"
        ),
    )


def plot_link_availability_time_series(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica la disponibilidad temporal ISL."""

    grouped = (
        group_snapshots_by_satellite(
            result
        )
    )

    markers = scenario_event_markers(
        result
    )

    scenario_name = (
        result_scenario_name(
            result
        )
    )

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    for (
        satellite_id,
        snapshots,
    ) in grouped.items():
        times = [
            snapshot_time_min(
                snapshot
            )
            for snapshot in snapshots
        ]

        availability = [
            1.0
            if bool(
                snapshot[
                    "link_available"
                ]
            )
            else 0.0
            for snapshot in snapshots
        ]

        axis.step(
            times,
            availability,
            where="post",
            label=satellite_id,
            linewidth=1.8,
        )

    add_event_markers(
        axis,
        markers,
    )

    axis.set_title(
        "Disponibilidad temporal del enlace ISL\n"
        f"Escenario: {scenario_name}"
    )

    axis.set_xlabel(
        "Tiempo de simulación [min]"
    )

    axis.set_ylabel(
        "Estado del enlace"
    )

    axis.set_ylim(
        -0.10,
        1.10,
    )

    axis.set_yticks(
        [
            0.0,
            1.0,
        ],
        labels=[
            "NO DISPONIBLE",
            "DISPONIBLE",
        ],
    )

    axis.grid(
        alpha=0.30,
    )

    axis.legend(
        loc="best"
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "04_disponibilidad_isl_temporal"
        ),
    )


def generate_temporal_charts_for_scenario(
    result_path: str | Path,
    output_directory: str | Path,
) -> dict[
    str,
    dict[str, Path],
]:
    """Genera las cuatro gráficas de un escenario."""

    result = load_scenario_result(
        result_path
    )

    return {
        "formation_error": (
            plot_formation_error_time_series(
                result=result,
                output_directory=(
                    output_directory
                ),
            )
        ),
        "soc": (
            plot_soc_time_series(
                result=result,
                output_directory=(
                    output_directory
                ),
            )
        ),
        "link_margin": (
            plot_link_margin_time_series(
                result=result,
                output_directory=(
                    output_directory
                ),
            )
        ),
        "link_availability": (
            plot_link_availability_time_series(
                result=result,
                output_directory=(
                    output_directory
                ),
            )
        ),
    }


def generate_all_temporal_charts(
    results_directory: str | Path,
    output_directory: str | Path,
) -> dict[
    str,
    dict[
        str,
        dict[str, Path],
    ],
]:
    """Genera las gráficas de los ocho escenarios."""

    results_path = Path(
        results_directory
    )

    output_path = Path(
        output_directory
    )

    generated_campaign: dict[
        str,
        dict[
            str,
            dict[str, Path],
        ],
    ] = {}

    for scenario in ScenarioName:
        scenario_result_path = (
            results_path
            / f"{scenario.value.lower()}.json"
        )

        scenario_output_directory = (
            output_path
            / scenario.value.lower()
        )

        generated_campaign[
            scenario.value
        ] = (
            generate_temporal_charts_for_scenario(
                result_path=(
                    scenario_result_path
                ),
                output_directory=(
                    scenario_output_directory
                ),
            )
        )

    return generated_campaign