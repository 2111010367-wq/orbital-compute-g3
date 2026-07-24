"""
Controlador temporal del dashboard G3.

Este módulo administra:

- Estado interno de reproducción.
- Línea temporal única por escenario.
- Inicio, pausa y reinicio.
- Avance sincronizado de la misión.
- Finalización automática.
- Formato del reloj de misión.

La animación avanza por tiempos únicos y no por
cada registro individual de satélite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


AnimationState = dict[str, Any]


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
    """Devuelve el primer campo disponible."""

    for key in keys:
        if key in mapping:
            return mapping[key]

    return default


def snapshot_time_s(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo de un snapshot en segundos."""

    value = first_available(
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

    numeric_value = safe_float(
        value,
        default=0.0,
    )

    if numeric_value is None:
        return 0.0

    return max(0.0, numeric_value)


def build_time_axis(
    result: Mapping[str, Any],
) -> list[float]:
    """
    Construye la línea temporal única del escenario.

    Ejemplo:

    183 snapshots de tres satélites producen
    aproximadamente 61 instantes temporales.
    """

    snapshots = result.get(
        "snapshots",
        [],
    )

    unique_times: set[float] = set()

    if not isinstance(
        snapshots,
        Sequence,
    ):
        return []

    for item in snapshots:
        if not isinstance(
            item,
            Mapping,
        ):
            continue

        time_s = snapshot_time_s(
            item
        )

        unique_times.add(
            round(time_s, 9)
        )

    return sorted(unique_times)


def calculate_progress_percent(
    time_index: int,
    time_count: int,
) -> float:
    """Calcula el avance porcentual de la misión."""

    if time_count <= 1:
        return (
            100.0
            if time_count == 1
            else 0.0
        )

    bounded_index = max(
        0,
        min(
            int(time_index),
            time_count - 1,
        ),
    )

    return (
        bounded_index
        / (time_count - 1)
        * 100.0
    )


def create_animation_state(
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """Crea el estado inicial de la animación."""

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    time_axis = build_time_axis(
        result
    )

    time_count = len(
        time_axis
    )

    initial_time_s = (
        time_axis[0]
        if time_axis
        else 0.0
    )

    return {
        "scenario": normalized_scenario,
        "time_index": 0,
        "time_s": initial_time_s,
        "time_count": time_count,
        "running": False,
        "completed": (
            time_count <= 1
        ),
        "tick_count": 0,
        "progress_percent": (
            calculate_progress_percent(
                time_index=0,
                time_count=time_count,
            )
        ),
    }


def normalize_animation_state(
    state: Mapping[str, Any] | None,
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """
    Normaliza un estado recibido desde dcc.Store.

    Si el escenario cambió, la animación se reinicia.
    """

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    time_axis = build_time_axis(
        result
    )

    if (
        not isinstance(state, Mapping)
        or str(
            state.get(
                "scenario",
                "",
            )
        ).strip().upper()
        != normalized_scenario
    ):
        return create_animation_state(
            scenario_name=(
                normalized_scenario
            ),
            result=result,
        )

    time_count = len(
        time_axis
    )

    if time_count == 0:
        return create_animation_state(
            scenario_name=(
                normalized_scenario
            ),
            result=result,
        )

    raw_index = state.get(
        "time_index",
        0,
    )

    try:
        time_index = int(
            raw_index
        )
    except (TypeError, ValueError):
        time_index = 0

    time_index = max(
        0,
        min(
            time_index,
            time_count - 1,
        ),
    )

    completed = bool(
        state.get(
            "completed",
            False,
        )
    )

    running = bool(
        state.get(
            "running",
            False,
        )
    )

    if time_index >= time_count - 1:
        completed = True

        if completed:
            running = False

    tick_count_value = state.get(
        "tick_count",
        0,
    )

    try:
        tick_count = max(
            0,
            int(tick_count_value),
        )
    except (TypeError, ValueError):
        tick_count = 0

    return {
        "scenario": normalized_scenario,
        "time_index": time_index,
        "time_s": time_axis[
            time_index
        ],
        "time_count": time_count,
        "running": running,
        "completed": completed,
        "tick_count": tick_count,
        "progress_percent": (
            calculate_progress_percent(
                time_index=time_index,
                time_count=time_count,
            )
        ),
    }


def start_animation(
    state: Mapping[str, Any] | None,
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """Inicia o reanuda la reproducción."""

    normalized_state = (
        normalize_animation_state(
            state=state,
            scenario_name=scenario_name,
            result=result,
        )
    )

    time_count = int(
        normalized_state[
            "time_count"
        ]
    )

    if time_count <= 1:
        normalized_state[
            "running"
        ] = False

        normalized_state[
            "completed"
        ] = True

        return normalized_state

    if normalized_state[
        "completed"
    ]:
        normalized_state[
            "time_index"
        ] = 0

        normalized_state[
            "time_s"
        ] = build_time_axis(
            result
        )[0]

        normalized_state[
            "tick_count"
        ] = 0

        normalized_state[
            "progress_percent"
        ] = 0.0

        normalized_state[
            "completed"
        ] = False

    normalized_state[
        "running"
    ] = True

    return normalized_state


def pause_animation(
    state: Mapping[str, Any] | None,
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """Pausa la reproducción en el instante actual."""

    normalized_state = (
        normalize_animation_state(
            state=state,
            scenario_name=scenario_name,
            result=result,
        )
    )

    normalized_state[
        "running"
    ] = False

    return normalized_state


def reset_animation(
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """Reinicia la misión en el primer instante."""

    return create_animation_state(
        scenario_name=scenario_name,
        result=result,
    )


def advance_animation(
    state: Mapping[str, Any] | None,
    scenario_name: str,
    result: Mapping[str, Any],
) -> AnimationState:
    """
    Avanza un instante temporal.

    Si la animación está pausada, mantiene el estado.
    Al llegar al último instante, se detiene.
    """

    normalized_state = (
        normalize_animation_state(
            state=state,
            scenario_name=scenario_name,
            result=result,
        )
    )

    if not normalized_state[
        "running"
    ]:
        return normalized_state

    time_axis = build_time_axis(
        result
    )

    if len(time_axis) <= 1:
        normalized_state[
            "running"
        ] = False

        normalized_state[
            "completed"
        ] = True

        return normalized_state

    current_index = int(
        normalized_state[
            "time_index"
        ]
    )

    final_index = len(
        time_axis
    ) - 1

    next_index = min(
        current_index + 1,
        final_index,
    )

    completed = (
        next_index >= final_index
    )

    normalized_state[
        "time_index"
    ] = next_index

    normalized_state[
        "time_s"
    ] = time_axis[
        next_index
    ]

    normalized_state[
        "tick_count"
    ] = int(
        normalized_state[
            "tick_count"
        ]
    ) + 1

    normalized_state[
        "completed"
    ] = completed

    normalized_state[
        "running"
    ] = not completed

    normalized_state[
        "progress_percent"
    ] = calculate_progress_percent(
        time_index=next_index,
        time_count=len(
            time_axis
        ),
    )

    return normalized_state


def format_mission_time(
    time_s: object,
) -> str:
    """Convierte segundos al formato T+HH:MM:SS."""

    numeric_time = safe_float(
        time_s,
        default=0.0,
    )

    if numeric_time is None:
        numeric_time = 0.0

    total_seconds = max(
        0,
        int(round(numeric_time)),
    )

    hours = (
        total_seconds // 3600
    )

    minutes = (
        total_seconds % 3600
    ) // 60

    seconds = (
        total_seconds % 60
    )

    return (
        f"T+{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )
def slice_result_until_time(
    result: Mapping[str, Any],
    target_time_s: object,
) -> dict[str, Any]:
    """
    Recorta un resultado hasta un instante determinado.

    Conserva únicamente los snapshots cuyo tiempo sea
    menor o igual que target_time_s.

    Ejemplo:

    target_time_s = 60

    Se conservarán los snapshots de:

    t = 0 s
    t = 60 s

    para los tres satélites.
    """

    numeric_target = safe_float(
        target_time_s,
        default=0.0,
    )

    if numeric_target is None:
        numeric_target = 0.0

    numeric_target = max(
        0.0,
        numeric_target,
    )

    original_snapshots = result.get(
        "snapshots",
        [],
    )

    selected_snapshots: list[
        dict[str, Any]
    ] = []

    if (
        isinstance(
            original_snapshots,
            Sequence,
        )
        and not isinstance(
            original_snapshots,
            (str, bytes),
        )
    ):
        for item in original_snapshots:
            if not isinstance(
                item,
                Mapping,
            ):
                continue

            item_time_s = snapshot_time_s(
                item
            )

            if (
                item_time_s
                <= numeric_target + 1e-9
            ):
                selected_snapshots.append(
                    dict(item)
                )

    sliced_result = dict(
        result
    )

    sliced_result[
        "snapshots"
    ] = selected_snapshots

    return sliced_result
def event_time_s(
    event: Mapping[str, Any],
) -> float:
    """
    Obtiene el tiempo de un evento en segundos.

    Admite eventos expresados en segundos o minutos.
    """

    second_keys = (
        "time_s",
        "simulation_time_s",
        "timestamp_s",
        "elapsed_time_s",
        "event_time_s",
        "t_s",
    )

    for key in second_keys:
        if key not in event:
            continue

        numeric_value = safe_float(
            event.get(key),
        )

        if numeric_value is not None:
            return max(
                0.0,
                numeric_value,
            )

    minute_keys = (
        "time_min",
        "simulation_time_min",
        "timestamp_min",
        "elapsed_time_min",
        "event_time_min",
    )

    for key in minute_keys:
        if key not in event:
            continue

        numeric_value = safe_float(
            event.get(key),
        )

        if numeric_value is not None:
            return max(
                0.0,
                numeric_value * 60.0,
            )

    return 0.0


def slice_events_until_time(
    result: Mapping[str, Any],
    target_time_s: object,
) -> list[dict[str, Any]]:
    """
    Selecciona los eventos ocurridos hasta un instante.

    No modifica el resultado original.
    """

    numeric_target = safe_float(
        target_time_s,
        default=0.0,
    )

    if numeric_target is None:
        numeric_target = 0.0

    numeric_target = max(
        0.0,
        numeric_target,
    )

    original_events = result.get(
        "events",
        [],
    )

    selected_events: list[
        dict[str, Any]
    ] = []

    if (
        not isinstance(
            original_events,
            Sequence,
        )
        or isinstance(
            original_events,
            (str, bytes),
        )
    ):
        return selected_events

    for item in original_events:
        if not isinstance(
            item,
            Mapping,
        ):
            continue

        if (
            event_time_s(item)
            <= numeric_target + 1e-9
        ):
            selected_events.append(
                dict(item)
            )

    selected_events.sort(
        key=event_time_s
    )

    return selected_events