"""
Gráficas temporales interactivas del dashboard G3.

Se representan:

- Error de formación.
- Estado de carga de la batería.
- Margen del enlace intersatelital en banda Ka.
- Disponibilidad del enlace ISL.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import plotly.graph_objects as go


SATELLITE_ORDER = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)

SATELLITE_COLORS = {
    "SAT-000": "#38bdf8",
    "SAT-001": "#a78bfa",
    "SAT-002": "#34d399",
}

PLOT_BACKGROUND = "#07111f"
PAPER_BACKGROUND = "#07111f"
GRID_COLOR = "rgba(148, 163, 184, 0.15)"
TEXT_COLOR = "#dbeafe"
MUTED_COLOR = "#94a3b8"


def safe_float(
    value: object,
    default: float | None = None,
) -> float | None:
    """Convierte un valor a número flotante."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_available(
    mapping: Mapping[str, Any],
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    """Obtiene el primer campo disponible."""

    for key in keys:
        if key in mapping:
            return mapping[key]

    return default


def normalize_soc_percent(
    value: object,
) -> float | None:
    """Normaliza el SOC al intervalo porcentual 0–100."""

    numeric_value = safe_float(value)

    if numeric_value is None:
        return None

    if -1.0 <= numeric_value <= 1.000001:
        return numeric_value * 100.0

    return numeric_value


def normalize_boolean(
    value: object,
    default: bool = False,
) -> bool:
    """Normaliza diferentes representaciones booleanas."""

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()

    if normalized in {
        "true",
        "1",
        "yes",
        "si",
        "sí",
        "available",
        "active",
        "online",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "unavailable",
        "inactive",
        "offline",
    }:
        return False

    return default


def snapshot_time_minutes(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo del snapshot en minutos."""

    time_s = first_available(
        snapshot,
        (
            "time_s",
            "simulation_time_s",
            "timestamp_s",
            "elapsed_time_s",
            "t_s",
            "time",
        ),
        default=0.0,
    )

    numeric_time = safe_float(
        time_s,
        default=0.0,
    )

    if numeric_time is None:
        return 0.0

    return numeric_time / 60.0


def snapshot_satellite_id(
    snapshot: Mapping[str, Any],
) -> str:
    """Obtiene el identificador del satélite."""

    value = first_available(
        snapshot,
        (
            "satellite_id",
            "node_id",
            "spacecraft_id",
            "client_id",
            "id",
        ),
        default="",
    )

    return str(value).strip()


def group_snapshots(
    snapshots: Sequence[Any],
) -> dict[str, list[Mapping[str, Any]]]:
    """Agrupa los snapshots por satélite y por tiempo."""

    grouped: dict[
        str,
        list[Mapping[str, Any]],
    ] = {}

    for item in snapshots:
        if not isinstance(item, Mapping):
            continue

        satellite_id = snapshot_satellite_id(
            item
        )

        if not satellite_id:
            continue

        grouped.setdefault(
            satellite_id,
            [],
        ).append(item)

    for satellite_snapshots in grouped.values():
        satellite_snapshots.sort(
            key=snapshot_time_minutes
        )

    return grouped


def ordered_satellite_ids(
    grouped: Mapping[
        str,
        Sequence[Mapping[str, Any]],
    ],
) -> list[str]:
    """Ordena primero los tres satélites principales."""

    result = [
        satellite_id
        for satellite_id in SATELLITE_ORDER
        if satellite_id in grouped
    ]

    extra_ids = sorted(
        satellite_id
        for satellite_id in grouped
        if satellite_id not in result
    )

    return result + extra_ids


def base_figure(
    title: str,
    y_title: str,
) -> go.Figure:
    """Crea una figura con estilo profesional común."""

    figure = go.Figure()

    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 17,
                "color": TEXT_COLOR,
            },
        },
        paper_bgcolor=PAPER_BACKGROUND,
        plot_bgcolor=PLOT_BACKGROUND,
        font={
            "family": (
                "Inter, Segoe UI, Arial, sans-serif"
            ),
            "color": TEXT_COLOR,
        },
        margin={
            "l": 62,
            "r": 24,
            "t": 62,
            "b": 52,
        },
        hovermode="x unified",
        legend={
            "orientation": "h",
            "x": 0.0,
            "y": 1.11,
            "font": {
                "color": TEXT_COLOR,
            },
        },
        xaxis={
            "title": {
                "text": (
                    "Tiempo de simulación [min]"
                ),
                "font": {
                    "color": TEXT_COLOR,
                },
            },
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "tickfont": {
                "color": MUTED_COLOR,
            },
        },
        yaxis={
            "title": {
                "text": y_title,
                "font": {
                    "color": TEXT_COLOR,
                },
            },
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "tickfont": {
                "color": MUTED_COLOR,
            },
        },
        transition={
            "duration": 350,
            "easing": "cubic-in-out",
        },
    )

    return figure


def add_no_data_annotation(
    figure: go.Figure,
) -> None:
    """Agrega una advertencia cuando no existen datos."""

    figure.add_annotation(
        text="No existen datos disponibles",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "size": 16,
            "color": MUTED_COLOR,
        },
    )


def build_formation_error_figure(
    result: Mapping[str, Any],
    scenario_name: str,
) -> go.Figure:
    """Construye el error de formación frente al tiempo."""

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots(
        snapshots
    )

    figure = base_figure(
        title=(
            "Error de formación — "
            f"{scenario_name}"
        ),
        y_title="Error de formación [m]",
    )

    for satellite_id in ordered_satellite_ids(
        grouped
    ):
        satellite_snapshots = grouped[
            satellite_id
        ]

        time_values: list[float] = []
        error_values: list[float | None] = []

        for snapshot in satellite_snapshots:
            time_values.append(
                snapshot_time_minutes(
                    snapshot
                )
            )

            error_values.append(
                safe_float(
                    first_available(
                        snapshot,
                        (
                            "formation_error_m",
                            "position_error_m",
                            "relative_error_m",
                            "error_m",
                        ),
                    )
                )
            )

        figure.add_trace(
            go.Scatter(
                x=time_values,
                y=error_values,
                mode="lines",
                name=satellite_id,
                line={
                    "width": 2.4,
                    "color": SATELLITE_COLORS.get(
                        satellite_id
                    ),
                },
                hovertemplate=(
                    f"{satellite_id}<br>"
                    "Tiempo: %{x:.1f} min<br>"
                    "Error: %{y:.4f} m"
                    "<extra></extra>"
                ),
            )
        )

    figure.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="#fbbf24",
        annotation_text="Umbral degradado: 0.5 m",
        annotation_position="top right",
    )

    if not grouped:
        add_no_data_annotation(figure)

    return figure


def build_soc_figure(
    result: Mapping[str, Any],
    scenario_name: str,
) -> go.Figure:
    """Construye la evolución temporal del SOC."""

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots(
        snapshots
    )

    figure = base_figure(
        title=(
            "Estado de carga de batería — "
            f"{scenario_name}"
        ),
        y_title="SOC [%]",
    )

    for satellite_id in ordered_satellite_ids(
        grouped
    ):
        satellite_snapshots = grouped[
            satellite_id
        ]

        time_values: list[float] = []
        soc_values: list[float | None] = []

        for snapshot in satellite_snapshots:
            time_values.append(
                snapshot_time_minutes(
                    snapshot
                )
            )

            soc_values.append(
                normalize_soc_percent(
                    first_available(
                        snapshot,
                        (
                            "soc",
                            "state_of_charge",
                            "battery_soc",
                            "soc_percent",
                        ),
                    )
                )
            )

        figure.add_trace(
            go.Scatter(
                x=time_values,
                y=soc_values,
                mode="lines",
                name=satellite_id,
                line={
                    "width": 2.4,
                    "color": SATELLITE_COLORS.get(
                        satellite_id
                    ),
                },
                hovertemplate=(
                    f"{satellite_id}<br>"
                    "Tiempo: %{x:.1f} min<br>"
                    "SOC: %{y:.2f} %"
                    "<extra></extra>"
                ),
            )
        )

    figure.add_hline(
        y=20.0,
        line_dash="dash",
        line_color="#fbbf24",
        annotation_text="Umbral degradado: 20 %",
        annotation_position="top right",
    )

    figure.add_hline(
        y=15.0,
        line_dash="dot",
        line_color="#fb7185",
        annotation_text="Umbral crítico: 15 %",
        annotation_position="bottom right",
    )

    figure.update_yaxes(
        range=[0.0, 105.0]
    )

    if not grouped:
        add_no_data_annotation(figure)

    return figure


def build_link_margin_figure(
    result: Mapping[str, Any],
    scenario_name: str,
) -> go.Figure:
    """Construye el margen del enlace Ka."""

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots(
        snapshots
    )

    figure = base_figure(
        title=(
            "Margen del enlace ISL en banda Ka — "
            f"{scenario_name}"
        ),
        y_title="Margen de enlace [dB]",
    )

    for satellite_id in ordered_satellite_ids(
        grouped
    ):
        satellite_snapshots = grouped[
            satellite_id
        ]

        time_values: list[float] = []
        margin_values: list[float | None] = []

        for snapshot in satellite_snapshots:
            time_values.append(
                snapshot_time_minutes(
                    snapshot
                )
            )

            margin_values.append(
                safe_float(
                    first_available(
                        snapshot,
                        (
                            "link_margin_db",
                            "margin_db",
                            "ka_margin_db",
                            "isl_margin_db",
                        ),
                    )
                )
            )

        figure.add_trace(
            go.Scatter(
                x=time_values,
                y=margin_values,
                mode="lines",
                name=satellite_id,
                line={
                    "width": 2.4,
                    "color": SATELLITE_COLORS.get(
                        satellite_id
                    ),
                },
                hovertemplate=(
                    f"{satellite_id}<br>"
                    "Tiempo: %{x:.1f} min<br>"
                    "Margen: %{y:.2f} dB"
                    "<extra></extra>"
                ),
            )
        )

    figure.add_hline(
        y=10.0,
        line_dash="dash",
        line_color="#fbbf24",
        annotation_text="Margen mínimo recomendado: 10 dB",
        annotation_position="top right",
    )

    figure.add_hline(
        y=0.0,
        line_dash="dot",
        line_color="#fb7185",
        annotation_text="Límite de disponibilidad: 0 dB",
        annotation_position="bottom right",
    )

    if not grouped:
        add_no_data_annotation(figure)

    return figure


def build_isl_availability_figure(
    result: Mapping[str, Any],
    scenario_name: str,
) -> go.Figure:
    """Construye la disponibilidad temporal del enlace."""

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots(
        snapshots
    )

    figure = base_figure(
        title=(
            "Disponibilidad del enlace "
            f"intersatelital — {scenario_name}"
        ),
        y_title="Estado del enlace",
    )

    for satellite_id in ordered_satellite_ids(
        grouped
    ):
        satellite_snapshots = grouped[
            satellite_id
        ]

        time_values: list[float] = []
        availability_values: list[int] = []

        for snapshot in satellite_snapshots:
            time_values.append(
                snapshot_time_minutes(
                    snapshot
                )
            )

            value = first_available(
                snapshot,
                (
                    "link_available",
                    "isl_available",
                    "communication_available",
                    "rf_available",
                ),
                default=True,
            )

            availability_values.append(
                1
                if normalize_boolean(
                    value,
                    default=True,
                )
                else 0
            )

        figure.add_trace(
            go.Scatter(
                x=time_values,
                y=availability_values,
                mode="lines",
                name=satellite_id,
                line={
                    "width": 2.7,
                    "shape": "hv",
                    "color": SATELLITE_COLORS.get(
                        satellite_id
                    ),
                },
                hovertemplate=(
                    f"{satellite_id}<br>"
                    "Tiempo: %{x:.1f} min<br>"
                    "Disponibilidad: %{customdata}"
                    "<extra></extra>"
                ),
                customdata=[
                    (
                        "Disponible"
                        if value == 1
                        else "No disponible"
                    )
                    for value
                    in availability_values
                ],
            )
        )

    figure.update_yaxes(
        range=[-0.15, 1.15],
        tickmode="array",
        tickvals=[0, 1],
        ticktext=[
            "NO DISPONIBLE",
            "DISPONIBLE",
        ],
    )

    if not grouped:
        add_no_data_annotation(figure)

    return figure


def build_temporal_figures(
    result: Mapping[str, Any],
    scenario_name: str,
) -> tuple[
    go.Figure,
    go.Figure,
    go.Figure,
    go.Figure,
]:
    """Genera las cuatro gráficas temporales."""

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    return (
        build_formation_error_figure(
            result=result,
            scenario_name=normalized_scenario,
        ),
        build_soc_figure(
            result=result,
            scenario_name=normalized_scenario,
        ),
        build_link_margin_figure(
            result=result,
            scenario_name=normalized_scenario,
        ),
        build_isl_availability_figure(
            result=result,
            scenario_name=normalized_scenario,
        ),
    )