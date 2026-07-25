"""
Visualización orbital 3D basada en los datos reales del simulador G3.

La figura representa:

- Posiciones relativas reales en metros.
- Trayectoria de cada satélite.
- Estado operacional.
- Disponibilidad de los enlaces ISL.
- SOC, margen Ka y error de formación.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

import plotly.graph_objects as go


SATELLITE_COLORS = {
    "SAT-000": "#38bdf8",
    "SAT-001": "#34d399",
    "SAT-002": "#fbbf24",
}

COLOR_OPERATIONAL = "#38bdf8"
COLOR_DEGRADED = "#fbbf24"
COLOR_FAILURE = "#fb7185"
COLOR_TRAJECTORY = "rgba(148, 163, 184, 0.48)"

BACKGROUND_COLOR = "#07111f"
TEXT_COLOR = "#dbeafe"
MUTED_COLOR = "#94a3b8"
GRID_COLOR = "rgba(148, 163, 184, 0.15)"


def safe_float(
    value: object,
    default: float | None = None,
) -> float | None:
    """Convierte un valor a float de forma segura."""

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


def parse_boolean(
    value: object,
    default: bool = False,
) -> bool:
    """Convierte diferentes formatos a booleano."""

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
        "active",
        "online",
        "available",
        "operational",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "inactive",
        "offline",
        "unavailable",
        "failed",
    }:
        return False

    return default


def safe_vector3(
    value: object,
) -> tuple[float, float, float] | None:
    """Convierte una lista o tupla en un vector 3D."""

    if not isinstance(value, Sequence):
        return None

    if isinstance(value, (str, bytes)):
        return None

    if len(value) < 3:
        return None

    x = safe_float(value[0])
    y = safe_float(value[1])
    z = safe_float(value[2])

    if x is None or y is None or z is None:
        return None

    return x, y, z


def snapshot_time_s(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo del snapshot en segundos."""

    value = first_available(
        snapshot,
        (
            "time_s",
            "simulation_time_s",
            "timestamp_s",
            "elapsed_time_s",
        ),
        default=0.0,
    )

    result = safe_float(
        value,
        default=0.0,
    )

    return 0.0 if result is None else result


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
            "id",
        ),
        default="",
    )

    return str(value).strip()


def snapshot_position_m(
    snapshot: Mapping[str, Any],
) -> tuple[float, float, float] | None:
    """Obtiene la posición relativa real en metros."""

    return safe_vector3(
        first_available(
            snapshot,
            (
                "position_m",
                "relative_position_m",
                "position",
            ),
        )
    )


def group_snapshots_by_satellite(
    snapshots: Sequence[Any],
) -> dict[str, list[Mapping[str, Any]]]:
    """Agrupa y ordena los snapshots por satélite."""

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

        position = snapshot_position_m(
            item
        )

        if not satellite_id or position is None:
            continue

        grouped.setdefault(
            satellite_id,
            [],
        ).append(item)

    for satellite_snapshots in grouped.values():
        satellite_snapshots.sort(
            key=snapshot_time_s
        )

    return grouped


def select_current_snapshots(
    grouped: Mapping[
        str,
        Sequence[Mapping[str, Any]],
    ],
    target_time_s: float | None = None,
) -> dict[str, Mapping[str, Any]]:
    """Selecciona un snapshot actual para cada satélite."""

    if target_time_s is None:
        available_times = [
            snapshot_time_s(snapshot)
            for satellite_snapshots
            in grouped.values()
            for snapshot
            in satellite_snapshots
        ]

        target_time_s = (
            max(available_times)
            if available_times
            else 0.0
        )

    selected: dict[
        str,
        Mapping[str, Any],
    ] = {}

    for satellite_id, satellite_snapshots in grouped.items():
        candidates = [
            snapshot
            for snapshot in satellite_snapshots
            if snapshot_time_s(snapshot)
            <= target_time_s
        ]

        if candidates:
            selected[satellite_id] = candidates[-1]
        elif satellite_snapshots:
            selected[satellite_id] = satellite_snapshots[0]

    return selected


def normalize_soc_percent(
    value: object,
) -> float | None:
    """Normaliza el SOC al intervalo porcentual."""

    numeric_value = safe_float(value)

    if numeric_value is None:
        return None

    if -1.0 <= numeric_value <= 1.000001:
        return numeric_value * 100.0

    return numeric_value


def satellite_state(
    snapshot: Mapping[str, Any],
) -> tuple[str, str]:
    """Determina el estado y color del satélite."""

    operational = parse_boolean(
        snapshot.get(
            "satellite_operational"
        ),
        default=True,
    )

    link_available = parse_boolean(
        snapshot.get(
            "link_available"
        ),
        default=True,
    )

    if not operational:
        return "FUERA DE SERVICIO", COLOR_FAILURE

    if not link_available:
        return "ENLACE DEGRADADO", COLOR_DEGRADED

    return "OPERATIVO", COLOR_OPERATIONAL


def format_optional(
    value: object,
    decimals: int = 2,
    suffix: str = "",
) -> str:
    """Formatea valores opcionales."""

    numeric_value = safe_float(value)

    if numeric_value is None:
        return "N/D"

    return (
        f"{numeric_value:.{decimals}f}"
        f"{suffix}"
    )

"""
Visualización orbital 3D basada en los datos reales del simulador G3.

La figura representa:

- Posiciones relativas reales en metros.
- Trayectoria de cada satélite.
- Estado operacional.
- Disponibilidad de los enlaces ISL.
- SOC, margen Ka y error de formación.
"""



from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

import plotly.graph_objects as go


SATELLITE_COLORS = {
    "SAT-000": "#38bdf8",
    "SAT-001": "#34d399",
    "SAT-002": "#fbbf24",
}

COLOR_OPERATIONAL = "#38bdf8"
COLOR_DEGRADED = "#fbbf24"
COLOR_FAILURE = "#fb7185"
COLOR_TRAJECTORY = "rgba(148, 163, 184, 0.48)"

BACKGROUND_COLOR = "#07111f"
TEXT_COLOR = "#dbeafe"
MUTED_COLOR = "#94a3b8"
GRID_COLOR = "rgba(148, 163, 184, 0.15)"


def safe_float(
    value: object,
    default: float | None = None,
) -> float | None:
    """Convierte un valor a float de forma segura."""

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


def parse_boolean(
    value: object,
    default: bool = False,
) -> bool:
    """Convierte diferentes formatos a booleano."""

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
        "active",
        "online",
        "available",
        "operational",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "inactive",
        "offline",
        "unavailable",
        "failed",
    }:
        return False

    return default


def safe_vector3(
    value: object,
) -> tuple[float, float, float] | None:
    """Convierte una lista o tupla en un vector 3D."""

    if not isinstance(value, Sequence):
        return None

    if isinstance(value, (str, bytes)):
        return None

    if len(value) < 3:
        return None

    x = safe_float(value[0])
    y = safe_float(value[1])
    z = safe_float(value[2])

    if x is None or y is None or z is None:
        return None

    return x, y, z


def snapshot_time_s(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo del snapshot en segundos."""

    value = first_available(
        snapshot,
        (
            "time_s",
            "simulation_time_s",
            "timestamp_s",
            "elapsed_time_s",
        ),
        default=0.0,
    )

    result = safe_float(
        value,
        default=0.0,
    )

    return 0.0 if result is None else result


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
            "id",
        ),
        default="",
    )

    return str(value).strip()


def snapshot_position_m(
    snapshot: Mapping[str, Any],
) -> tuple[float, float, float] | None:
    """Obtiene la posición relativa real en metros."""

    return safe_vector3(
        first_available(
            snapshot,
            (
                "position_m",
                "relative_position_m",
                "position",
            ),
        )
    )


def group_snapshots_by_satellite(
    snapshots: Sequence[Any],
) -> dict[str, list[Mapping[str, Any]]]:
    """Agrupa y ordena los snapshots por satélite."""

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

        position = snapshot_position_m(
            item
        )

        if not satellite_id or position is None:
            continue

        grouped.setdefault(
            satellite_id,
            [],
        ).append(item)

    for satellite_snapshots in grouped.values():
        satellite_snapshots.sort(
            key=snapshot_time_s
        )

    return grouped


def select_current_snapshots(
    grouped: Mapping[
        str,
        Sequence[Mapping[str, Any]],
    ],
    target_time_s: float | None = None,
) -> dict[str, Mapping[str, Any]]:
    """Selecciona un snapshot actual para cada satélite."""

    if target_time_s is None:
        available_times = [
            snapshot_time_s(snapshot)
            for satellite_snapshots
            in grouped.values()
            for snapshot
            in satellite_snapshots
        ]

        target_time_s = (
            max(available_times)
            if available_times
            else 0.0
        )

    selected: dict[
        str,
        Mapping[str, Any],
    ] = {}

    for satellite_id, satellite_snapshots in grouped.items():
        candidates = [
            snapshot
            for snapshot in satellite_snapshots
            if snapshot_time_s(snapshot)
            <= target_time_s
        ]

        if candidates:
            selected[satellite_id] = candidates[-1]
        elif satellite_snapshots:
            selected[satellite_id] = satellite_snapshots[0]

    return selected


def normalize_soc_percent(
    value: object,
) -> float | None:
    """Normaliza el SOC al intervalo porcentual."""

    numeric_value = safe_float(value)

    if numeric_value is None:
        return None

    if -1.0 <= numeric_value <= 1.000001:
        return numeric_value * 100.0

    return numeric_value


def satellite_state(
    snapshot: Mapping[str, Any],
) -> tuple[str, str]:
    """Determina el estado y color del satélite."""

    operational = parse_boolean(
        snapshot.get(
            "satellite_operational"
        ),
        default=True,
    )

    link_available = parse_boolean(
        snapshot.get(
            "link_available"
        ),
        default=True,
    )

    if not operational:
        return "FUERA DE SERVICIO", COLOR_FAILURE

    if not link_available:
        return "ENLACE DEGRADADO", COLOR_DEGRADED

    return "OPERATIVO", COLOR_OPERATIONAL


def format_optional(
    value: object,
    decimals: int = 2,
    suffix: str = "",
) -> str:
    """Formatea valores opcionales."""

    numeric_value = safe_float(value)

    if numeric_value is None:
        return "N/D"

    return (
        f"{numeric_value:.{decimals}f}"
        f"{suffix}"
    )

def apply_professional_orbit_style(
    figure: go.Figure,
    scenario_name: str,
) -> go.Figure:
    """
    Aplica una presentación profesional a la formación orbital 3D.

    No modifica posiciones, errores ni trayectorias.
    Solamente controla cámara, ejes, fondo y proporciones.
    """

    axis_font = {
        "color": "#b8c9d8",
        "size": 10,
    }

    axis_title_font = {
        "color": "#d8e8f5",
        "size": 11,
    }

    common_axis = {
        "showbackground": False,
        "backgroundcolor": "rgba(0,0,0,0)",
        "showgrid": True,
        "gridcolor": "rgba(125, 211, 252, 0.11)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linecolor": "rgba(125, 211, 252, 0.28)",
        "linewidth": 1,
        "showspikes": False,
        "ticks": "outside",
        "tickfont": axis_font,
    }

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={
            "l": 0,
            "r": 0,
            "t": 58,
            "b": 4,
        },
        hoverlabel={
            "bgcolor": "#071827",
            "bordercolor": "#38bdf8",
            "font": {
                "color": "#e6f7ff",
                "size": 12,
            },
        },
        legend={
            "orientation": "h",
            "x": 0.0,
            "xanchor": "left",
            "y": 1.02,
            "yanchor": "bottom",
            "bgcolor": "rgba(0,0,0,0)",
            "font": {
                "color": "#d9e8f3",
                "size": 11,
            },
        },
        scene={
            "bgcolor": "#07111f",
            "dragmode": "orbit",
            "aspectmode": "manual",
            "aspectratio": {
                "x": 1.75,
                "y": 1.05,
                "z": 0.72,
            },
            "xaxis": {
                **common_axis,
                "title": {
                    "text": "X relativo [m]",
                    "font": axis_title_font,
                },
            },
            "yaxis": {
                **common_axis,
                "title": {
                    "text": "Y relativo [m]",
                    "font": axis_title_font,
                },
            },
            "zaxis": {
                **common_axis,
                "title": {
                    "text": "Z relativo [m]",
                    "font": axis_title_font,
                },
            },
            "camera": {
                "eye": {
                    "x": 1.55,
                    "y": 1.30,
                    "z": 0.90,
                },
                "center": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": -0.04,
                },
                "up": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 1.0,
                },
            },
        },
        uirevision=f"professional-orbit-{scenario_name}",
    )

    return figure
def build_orbit_3d_figure(
    result: Mapping[str, Any],
    scenario_name: str,
    target_time_s: float | None = None,
) -> go.Figure:
    """
    Construye la formación orbital tridimensional.

    Las coordenadas se representan en el marco relativo
    de la formación y se mantienen en metros reales.
    """

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots_by_satellite(
        snapshots
    )

    current = select_current_snapshots(
        grouped=grouped,
        target_time_s=target_time_s,
    )

    figure = go.Figure()

    # Trayectorias históricas reales
    for satellite_id, satellite_snapshots in grouped.items():
        trajectory = [
            snapshot_position_m(snapshot)
            for snapshot in satellite_snapshots
        ]

        trajectory = [
            position
            for position in trajectory
            if position is not None
        ]

        if not trajectory:
            continue

        x_values = [
            position[0]
            for position in trajectory
        ]

        y_values = [
            position[1]
            for position in trajectory
        ]

        z_values = [
            position[2]
            for position in trajectory
        ]

        figure.add_trace(
            go.Scatter3d(
                x=x_values,
                y=y_values,
                z=z_values,
                mode="lines",
                name=(
                    f"Trayectoria {satellite_id}"
                ),
                line={
                    "color": (
                        SATELLITE_COLORS.get(
                            satellite_id,
                            COLOR_TRAJECTORY,
                        )
                    ),
                    "width": 3,
                },
                opacity=0.55,
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # Enlaces ISL entre los satélites actuales
    for satellite_a, satellite_b in combinations(
        sorted(current.keys()),
        2,
    ):
        snapshot_a = current[satellite_a]
        snapshot_b = current[satellite_b]

        position_a = snapshot_position_m(
            snapshot_a
        )

        position_b = snapshot_position_m(
            snapshot_b
        )

        if position_a is None or position_b is None:
            continue

        operational_a = parse_boolean(
            snapshot_a.get(
                "satellite_operational"
            ),
            default=True,
        )

        operational_b = parse_boolean(
            snapshot_b.get(
                "satellite_operational"
            ),
            default=True,
        )

        link_a = parse_boolean(
            snapshot_a.get(
                "link_available"
            ),
            default=True,
        )

        link_b = parse_boolean(
            snapshot_b.get(
                "link_available"
            ),
            default=True,
        )

        if not operational_a or not operational_b:
            link_color = COLOR_FAILURE
            link_state = "Interrumpido"
            link_dash = "dot"
        elif not link_a or not link_b:
            link_color = COLOR_DEGRADED
            link_state = "Degradado"
            link_dash = "dash"
        else:
            link_color = "#5ce1e6"
            link_state = "Disponible"
            link_dash = "solid"

        figure.add_trace(
            go.Scatter3d(
                x=[
                    position_a[0],
                    position_b[0],
                ],
                y=[
                    position_a[1],
                    position_b[1],
                ],
                z=[
                    position_a[2],
                    position_b[2],
                ],
                mode="lines",
                name=(
                    f"ISL {satellite_a}"
                    f"–{satellite_b}"
                ),
                line={
                    "color": link_color,
                    "width": 6,
                    "dash": link_dash,
                },
                hovertemplate=(
                    f"<b>{satellite_a}"
                    f" ↔ {satellite_b}</b>"
                    f"<br>Estado: {link_state}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # Posición actual de cada satélite
    marker_x: list[float] = []
    marker_y: list[float] = []
    marker_z: list[float] = []
    marker_colors: list[str] = []
    marker_labels: list[str] = []
    custom_data: list[list[Any]] = []

    for satellite_id in sorted(current.keys()):
        snapshot = current[satellite_id]

        position = snapshot_position_m(
            snapshot
        )

        if position is None:
            continue

        state_text, state_color = (
            satellite_state(snapshot)
        )

        soc_percent = normalize_soc_percent(
            snapshot.get("soc")
        )

        marker_x.append(position[0])
        marker_y.append(position[1])
        marker_z.append(position[2])
        marker_colors.append(state_color)
        marker_labels.append(satellite_id)

        custom_data.append(
            [
                snapshot_time_s(snapshot)
                / 60.0,
                (
                    soc_percent
                    if soc_percent is not None
                    else float("nan")
                ),
                safe_float(
                    snapshot.get(
                        "link_margin_db"
                    ),
                    default=float("nan"),
                ),
                safe_float(
                    snapshot.get(
                        "formation_error_m"
                    ),
                    default=float("nan"),
                ),
                state_text,
                position[0],
                position[1],
                position[2],
            ]
        )

    figure.add_trace(
        go.Scatter3d(
            x=marker_x,
            y=marker_y,
            z=marker_z,
            mode="markers+text",
            name="Formación actual",
            text=marker_labels,
            textposition="top center",
            textfont={
                "color": TEXT_COLOR,
                "size": 12,
            },
            marker={
                "size": 10,
                "color": marker_colors,
                "line": {
                    "color": "#ffffff",
                    "width": 1.4,
                },
                "symbol": "diamond",
            },
            customdata=custom_data,
            hovertemplate=(
                "<b>%{text}</b>"
                "<br>Estado: %{customdata[4]}"
                "<br>Tiempo: %{customdata[0]:.1f} min"
                "<br>SOC: %{customdata[1]:.2f} %"
                "<br>Margen Ka: %{customdata[2]:.2f} dB"
                "<br>Error: %{customdata[3]:.4f} m"
                "<br>X: %{customdata[5]:.4f} m"
                "<br>Y: %{customdata[6]:.4f} m"
                "<br>Z: %{customdata[7]:.4f} m"
                "<extra></extra>"
            ),
        )
    )

    if not current:
        figure.add_annotation(
            text=(
                "No existen posiciones orbitales "
                "disponibles"
            ),
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

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    figure.update_layout(
        title={
            "text": (
                "Formación orbital 3D relativa — "
                f"{normalized_scenario}"
            ),
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 17,
                "color": TEXT_COLOR,
            },
        },
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font={
            "family": (
                "Inter, Segoe UI, Arial, sans-serif"
            ),
            "color": TEXT_COLOR,
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 70,
            "b": 0,
        },
        legend={
            "orientation": "h",
            "x": 0.0,
            "y": 1.03,
            "font": {
                "color": TEXT_COLOR,
            },
        },
        uirevision=(
            f"orbit-3d-{normalized_scenario}"
        ),
        scene={
            "bgcolor": BACKGROUND_COLOR,
            "aspectmode": "data",
            "xaxis": {
                "title": {
                    "text": "X relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "yaxis": {
                "title": {
                    "text": "Y relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "zaxis": {
                "title": {
                    "text": "Z relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "camera": {
                "eye": {
                    "x": 1.55,
                    "y": 1.40,
                    "z": 0.95,
                }
            },
            "annotations": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "text": (
                        "Marco relativo de formación"
                    ),
                    "showarrow": True,
                    "arrowcolor": "#38bdf8",
                    "font": {
                        "color": MUTED_COLOR,
                        "size": 10,
                    },
                }
            ],
        },
    )
    return figure



def build_orbit_3d_figure(
    result: Mapping[str, Any],
    scenario_name: str,
    target_time_s: float | None = None,
) -> go.Figure:
    """
    Construye la formación orbital tridimensional.

    Las coordenadas se representan en el marco relativo
    de la formación y se mantienen en metros reales.
    """

    snapshots = result.get(
        "snapshots",
        [],
    )

    grouped = group_snapshots_by_satellite(
        snapshots
    )

    current = select_current_snapshots(
        grouped=grouped,
        target_time_s=target_time_s,
    )

    figure = go.Figure()

    # Trayectorias históricas reales
    for satellite_id, satellite_snapshots in grouped.items():
        trajectory = [
            snapshot_position_m(snapshot)
            for snapshot in satellite_snapshots
        ]

        trajectory = [
            position
            for position in trajectory
            if position is not None
        ]

        if not trajectory:
            continue

        x_values = [
            position[0]
            for position in trajectory
        ]

        y_values = [
            position[1]
            for position in trajectory
        ]

        z_values = [
            position[2]
            for position in trajectory
        ]

        figure.add_trace(
            go.Scatter3d(
                x=x_values,
                y=y_values,
                z=z_values,
                mode="lines",
                name=(
                    f"Trayectoria {satellite_id}"
                ),
                line={
                    "color": (
                        SATELLITE_COLORS.get(
                            satellite_id,
                            COLOR_TRAJECTORY,
                        )
                    ),
                    "width": 3,
                },
                opacity=0.55,
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # Enlaces ISL entre los satélites actuales
    for satellite_a, satellite_b in combinations(
        sorted(current.keys()),
        2,
    ):
        snapshot_a = current[satellite_a]
        snapshot_b = current[satellite_b]

        position_a = snapshot_position_m(
            snapshot_a
        )

        position_b = snapshot_position_m(
            snapshot_b
        )

        if position_a is None or position_b is None:
            continue

        operational_a = parse_boolean(
            snapshot_a.get(
                "satellite_operational"
            ),
            default=True,
        )

        operational_b = parse_boolean(
            snapshot_b.get(
                "satellite_operational"
            ),
            default=True,
        )

        link_a = parse_boolean(
            snapshot_a.get(
                "link_available"
            ),
            default=True,
        )

        link_b = parse_boolean(
            snapshot_b.get(
                "link_available"
            ),
            default=True,
        )

        if not operational_a or not operational_b:
            link_color = COLOR_FAILURE
            link_state = "Interrumpido"
            link_dash = "dot"
        elif not link_a or not link_b:
            link_color = COLOR_DEGRADED
            link_state = "Degradado"
            link_dash = "dash"
        else:
            link_color = "#5ce1e6"
            link_state = "Disponible"
            link_dash = "solid"

        figure.add_trace(
            go.Scatter3d(
                x=[
                    position_a[0],
                    position_b[0],
                ],
                y=[
                    position_a[1],
                    position_b[1],
                ],
                z=[
                    position_a[2],
                    position_b[2],
                ],
                mode="lines",
                name=(
                    f"ISL {satellite_a}"
                    f"–{satellite_b}"
                ),
                line={
                    "color": link_color,
                    "width": 6,
                    "dash": link_dash,
                },
                hovertemplate=(
                    f"<b>{satellite_a}"
                    f" ↔ {satellite_b}</b>"
                    f"<br>Estado: {link_state}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # Posición actual de cada satélite
    marker_x: list[float] = []
    marker_y: list[float] = []
    marker_z: list[float] = []
    marker_colors: list[str] = []
    marker_labels: list[str] = []
    custom_data: list[list[Any]] = []

    for satellite_id in sorted(current.keys()):
        snapshot = current[satellite_id]

        position = snapshot_position_m(
            snapshot
        )

        if position is None:
            continue

        state_text, state_color = (
            satellite_state(snapshot)
        )

        soc_percent = normalize_soc_percent(
            snapshot.get("soc")
        )

        marker_x.append(position[0])
        marker_y.append(position[1])
        marker_z.append(position[2])
        marker_colors.append(state_color)
        marker_labels.append(satellite_id)

        custom_data.append(
            [
                snapshot_time_s(snapshot)
                / 60.0,
                (
                    soc_percent
                    if soc_percent is not None
                    else float("nan")
                ),
                safe_float(
                    snapshot.get(
                        "link_margin_db"
                    ),
                    default=float("nan"),
                ),
                safe_float(
                    snapshot.get(
                        "formation_error_m"
                    ),
                    default=float("nan"),
                ),
                state_text,
                position[0],
                position[1],
                position[2],
            ]
        )

    figure.add_trace(
        go.Scatter3d(
            x=marker_x,
            y=marker_y,
            z=marker_z,
            mode="markers+text",
            name="Formación actual",
            text=marker_labels,
            textposition="top center",
            textfont={
                "color": TEXT_COLOR,
                "size": 12,
            },
            marker={
                "size": 10,
                "color": marker_colors,
                "line": {
                    "color": "#ffffff",
                    "width": 1.4,
                },
                "symbol": "diamond",
            },
            customdata=custom_data,
            hovertemplate=(
                "<b>%{text}</b>"
                "<br>Estado: %{customdata[4]}"
                "<br>Tiempo: %{customdata[0]:.1f} min"
                "<br>SOC: %{customdata[1]:.2f} %"
                "<br>Margen Ka: %{customdata[2]:.2f} dB"
                "<br>Error: %{customdata[3]:.4f} m"
                "<br>X: %{customdata[5]:.4f} m"
                "<br>Y: %{customdata[6]:.4f} m"
                "<br>Z: %{customdata[7]:.4f} m"
                "<extra></extra>"
            ),
        )
    )

    if not current:
        figure.add_annotation(
            text=(
                "No existen posiciones orbitales "
                "disponibles"
            ),
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

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    figure.update_layout(
        title={
            "text": (
                "Formación orbital 3D relativa — "
                f"{normalized_scenario}"
            ),
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 17,
                "color": TEXT_COLOR,
            },
        },
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font={
            "family": (
                "Inter, Segoe UI, Arial, sans-serif"
            ),
            "color": TEXT_COLOR,
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 70,
            "b": 0,
        },
        legend={
            "orientation": "h",
            "x": 0.0,
            "y": 1.03,
            "font": {
                "color": TEXT_COLOR,
            },
        },
        uirevision=(
            f"orbit-3d-{normalized_scenario}"
        ),
        scene={
            "bgcolor": BACKGROUND_COLOR,
            "aspectmode": "data",
            "xaxis": {
                "title": {
                    "text": "X relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "yaxis": {
                "title": {
                    "text": "Y relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "zaxis": {
                "title": {
                    "text": "Z relativo [m]",
                    "font": {
                        "color": TEXT_COLOR,
                    },
                },
                "gridcolor": GRID_COLOR,
                "zerolinecolor": GRID_COLOR,
                "tickfont": {
                    "color": MUTED_COLOR,
                },
            },
            "camera": {
                "eye": {
                    "x": 1.55,
                    "y": 1.40,
                    "z": 0.95,
                }
            },
            "annotations": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "text": (
                        "Marco relativo de formación"
                    ),
                    "showarrow": True,
                    "arrowcolor": "#38bdf8",
                    "font": {
                        "color": MUTED_COLOR,
                        "size": 10,
                    },
                }
            ],
        },
    )

    figure = apply_professional_orbit_style(
    figure=figure,
    scenario_name=scenario_name,
    )

    return figure