"""
Callbacks dinámicos del dashboard profesional G3.

Esta capa conecta el selector de escenarios con:

- KPI generales.
- Evaluación de resiliencia.
- Telemetría final de los satélites.
- Estado operacional.
- Registro de eventos cognitivos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from dash import (
    Dash,
    Input,
    Output,
    State,
    ctx,
    html,
    no_update,
)
from dash.exceptions import PreventUpdate

from dashboard_g3.layout import (
    SCENARIO_LABELS,
    assessment_level,
    assessment_score,
    build_event_feed,
    first_available,
    format_number,
)
from dashboard_g3.animation import (
    advance_animation,
    format_mission_time,
    normalize_animation_state,
    pause_animation,
    reset_animation,
    slice_events_until_time,
    slice_result_until_time,
    start_animation,
)
from dashboard_g3.figures.orbit_3d import (
    build_orbit_3d_figure,
)
from dashboard_g3.figures.temporal import (
    build_temporal_figures,
)
DEFAULT_SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)


def parse_boolean(
    value: object,
    default: bool = False,
) -> bool:
    """Convierte distintos formatos a booleano."""

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
        "on",
        "enabled",
        "active",
        "available",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "off",
        "disabled",
        "inactive",
        "unavailable",
    }:
        return False

    return default


def safe_float(
    value: object,
    default: float | None = None,
) -> float | None:
    """Convierte un valor a número flotante."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_soc_percent(
    value: object,
) -> float | None:
    """
    Normaliza el estado de carga a porcentaje.

    El simulador normalmente guarda SOC entre 0 y 1.
    También se acepta un valor previamente expresado
    entre 0 y 100.
    """

    numeric_value = safe_float(value)

    if numeric_value is None:
        return None

    if -1.0 <= numeric_value <= 1.000001:
        return numeric_value * 100.0

    return numeric_value


def snapshot_time_s(
    snapshot: Mapping[str, Any],
) -> float:
    """Obtiene el tiempo de un snapshot."""

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
            "client_id",
            "id",
        ),
        default="",
    )

    return str(value).strip()


def latest_snapshots_by_satellite(
    snapshots: Sequence[Any],
) -> dict[str, Mapping[str, Any]]:
    """Obtiene el último snapshot de cada satélite."""

    latest: dict[
        str,
        Mapping[str, Any],
    ] = {}

    for item in snapshots:
        if not isinstance(item, Mapping):
            continue

        satellite_id = snapshot_satellite_id(
            item
        )

        if not satellite_id:
            continue

        previous = latest.get(
            satellite_id
        )

        if (
            previous is None
            or snapshot_time_s(item)
            >= snapshot_time_s(previous)
        ):
            latest[satellite_id] = item

    return latest


def satellite_is_disabled(
    snapshot: Mapping[str, Any],
) -> bool:
    """Determina si un satélite está deshabilitado."""

    failure_value = first_available(
        snapshot,
        (
            "satellite_failed",
            "node_failed",
            "is_failed",
            "failed",
            "satellite_disabled",
            "node_disabled",
            "disabled",
        ),
        default=None,
    )

    if failure_value is not None:
        if parse_boolean(
            failure_value,
            default=False,
        ):
            return True

    enabled_value = first_available(
        snapshot,
        (
            "satellite_enabled",
            "node_enabled",
            "control_enabled",
            "is_active",
            "active",
            "enabled",
        ),
        default=None,
    )

    if enabled_value is not None:
        return not parse_boolean(
            enabled_value,
            default=True,
        )

    mode_value = first_available(
        snapshot,
        (
            "operational_mode",
            "mode",
            "state",
            "status",
        ),
        default="",
    )

    normalized_mode = (
        str(mode_value)
        .strip()
        .upper()
    )

    return normalized_mode in {
        "FAILED",
        "FAILURE",
        "DISABLED",
        "OFFLINE",
        "INACTIVE",
        "FUERA_DE_SERVICIO",
        "FUERA DE SERVICIO",
    }


def satellite_link_available(
    snapshot: Mapping[str, Any],
) -> bool:
    """Obtiene la disponibilidad del enlace."""

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

    return parse_boolean(
        value,
        default=True,
    )


def satellite_operational_state(
    snapshot: Mapping[str, Any],
) -> tuple[str, str, str]:
    """
    Clasifica el estado operacional.

    Retorna:

    - Texto del estado.
    - Clase CSS de la insignia.
    - Clase CSS de la tarjeta.
    """

    if satellite_is_disabled(snapshot):
        return (
            "FUERA DE SERVICIO",
            "status-offline",
            "satellite-card-offline",
        )

    soc_percent = normalize_soc_percent(
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

    link_available = (
        satellite_link_available(
            snapshot
        )
    )

    if (
        not link_available
        or (
            soc_percent is not None
            and soc_percent < 20.0
        )
    ):
        return (
            "DEGRADADO",
            "status-degraded",
            "satellite-card-degraded",
        )

    return (
        "EN LÍNEA",
        "status-online",
        "satellite-card-online",
    )


def format_soc(
    snapshot: Mapping[str, Any],
) -> str:
    """Formatea el SOC del satélite."""

    value = first_available(
        snapshot,
        (
            "soc",
            "state_of_charge",
            "battery_soc",
            "soc_percent",
        ),
    )

    percent = normalize_soc_percent(
        value
    )

    if percent is None:
        return "N/D"

    return f"{percent:.1f} %"


def format_link_margin(
    snapshot: Mapping[str, Any],
) -> str:
    """Formatea el margen del enlace Ka."""

    value = first_available(
        snapshot,
        (
            "link_margin_db",
            "margin_db",
            "ka_margin_db",
            "isl_margin_db",
        ),
    )

    numeric_value = safe_float(value)

    if numeric_value is None:
        return "N/D"

    return f"{numeric_value:.2f} dB"


def format_formation_error(
    snapshot: Mapping[str, Any],
) -> str:
    """Formatea el error de formación."""

    value = first_available(
        snapshot,
        (
            "formation_error_m",
            "position_error_m",
            "relative_error_m",
            "error_m",
        ),
    )

    numeric_value = safe_float(value)

    if numeric_value is None:
        return "N/D"

    return f"{numeric_value:.3f} m"


def build_telemetry_cards(
    summary: Mapping[str, Any],
    snapshots: Sequence[Any],
) -> list[html.Div]:
    """Construye la telemetría final del escenario."""

    latest_snapshots = (
        latest_snapshots_by_satellite(
            snapshots
        )
    )

    summary_satellite_ids = (
        summary.get(
            "satellite_ids",
            [],
        )
    )

    satellite_ids = [
        str(satellite_id)
        for satellite_id
        in summary_satellite_ids
        if str(satellite_id).strip()
    ]

    if not satellite_ids:
        satellite_ids = list(
            latest_snapshots.keys()
        )

    if not satellite_ids:
        satellite_ids = list(
            DEFAULT_SATELLITE_IDS
        )

    cards: list[html.Div] = []

    for index, satellite_id in enumerate(
        satellite_ids
    ):
        snapshot = latest_snapshots.get(
            satellite_id,
            {},
        )

        if index == 0:
            role = "Líder de formación"
        else:
            role = f"Seguidor {index}"

        (
            operational_state,
            badge_class,
            card_class,
        ) = satellite_operational_state(
            snapshot
        )

        cards.append(
            html.Div(
                className=(
                    "satellite-card "
                    f"{card_class}"
                ),
                children=[
                    html.Div(
                        className=(
                            "satellite-card-header"
                        ),
                        children=[
                            html.Div(
                                satellite_id,
                                className=(
                                    "satellite-name"
                                ),
                            ),
                            html.Div(
                                operational_state,
                                id=(
                                    f"satellite-{index}"
                                    "-status"
                                ),
                                className=(
                                    "status-badge "
                                    f"{badge_class}"
                                ),
                            ),
                        ],
                    ),
                    html.Div(
                        role,
                        className="satellite-role",
                    ),
                    html.Div(
                        className=(
                            "satellite-mini-grid"
                        ),
                        children=[
                            html.Div(
                                [
                                    html.Span(
                                        "SOC",
                                        className=(
                                            "mini-label"
                                        ),
                                    ),
                                    html.Strong(
                                        format_soc(
                                            snapshot
                                        ),
                                        id=(
                                            f"satellite-{index}"
                                            "-soc"
                                        ),
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Margen Ka",
                                        className=(
                                            "mini-label"
                                        ),
                                    ),
                                    html.Strong(
                                        format_link_margin(
                                            snapshot
                                        ),
                                        id=(
                                            f"satellite-{index}"
                                            "-margin"
                                        ),
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Error",
                                        className=(
                                            "mini-label"
                                        ),
                                    ),
                                    html.Strong(
                                        format_formation_error(
                                            snapshot
                                        ),
                                        id=(
                                            f"satellite-{index}"
                                            "-error"
                                        ),
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            )
        )

    return cards


def build_scenario_view(
    dataset: Mapping[str, Any],
    scenario_name: str,
) -> dict[str, Any]:
    """Construye todos los valores visibles del escenario."""

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    scenarios = dataset.get(
        "scenarios",
        {},
    )

    summaries = dataset.get(
        "scenario_summaries",
        {},
    )

    assessments = dataset.get(
        "assessment",
        {},
    )

    if normalized_scenario not in scenarios:
        raise KeyError(
            "Escenario desconocido: "
            f"{normalized_scenario}"
        )

    if normalized_scenario not in summaries:
        raise KeyError(
            "No existe resumen para: "
            f"{normalized_scenario}"
        )

    if normalized_scenario not in assessments:
        raise KeyError(
            "No existe evaluación para: "
            f"{normalized_scenario}"
        )

    result = scenarios[
        normalized_scenario
    ]

    (
        formation_figure,
        soc_figure,
        link_margin_figure,
        isl_availability_figure,
      ) = build_temporal_figures(
        result=result,
        scenario_name=normalized_scenario,
    )
    orbit_figure = build_orbit_3d_figure(
        result=result,
        scenario_name=normalized_scenario,
    )
    summary = summaries[
        normalized_scenario
    ]

    assessment = assessments[
        normalized_scenario
    ]

    snapshots = result.get(
        "snapshots",
        [],
    )

    events = result.get(
        "events",
        [],
    )

    if not isinstance(snapshots, list):
        snapshots = list(snapshots)

    if not isinstance(events, list):
        events = list(events)

    satellite_count = summary.get(
        "satellite_count",
        len(
            latest_snapshots_by_satellite(
                snapshots
            )
        ),
    )

    duration_min = summary.get(
        "duration_min",
        0.0,
    )

    snapshot_count = summary.get(
        "snapshot_count",
        len(snapshots),
    )

    event_count = summary.get(
        "event_count",
        len(events),
    )

    scenario_label = (
        SCENARIO_LABELS.get(
            normalized_scenario,
            normalized_scenario,
        )
    )

    return {
        "satellite_count": str(
            satellite_count
        ),
        "duration": format_number(
            duration_min,
            decimals=1,
        ),
        "snapshot_count": str(
            snapshot_count
        ),
        "event_count": str(
            event_count
        ),
        "resilience_score": (
            assessment_score(
                assessment
            )
        ),
        "classification": (
            assessment_level(
                assessment
            )
        ),
        "active_scenario": (
            f"{normalized_scenario} · "
            f"{scenario_label}"
        ),
        "event_count_badge": str(
            event_count
        ),
        "telemetry": (
            build_telemetry_cards(
                summary=summary,
                snapshots=snapshots,
            )
        ),
            "event_feed": (
            build_event_feed(
                events
            )
        ),
        "orbit_figure": orbit_figure,
        "formation_figure": (
            formation_figure
        ),
        "soc_figure": (
            soc_figure
        ),
        "link_margin_figure": (
            link_margin_figure
        ),
        "isl_availability_figure": (
            isl_availability_figure
        ),
    }

def build_live_telemetry_view(
    dataset: Mapping[str, Any],
    scenario_name: str,
    target_time_s: object,
) -> Any:
    """
    Construye la telemetría correspondiente al reloj.

    Se reutiliza el constructor existente de tarjetas,
    pero se le entrega solamente la información disponible
    hasta el instante actual de la misión.
    """

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    scenarios = dataset.get(
        "scenarios",
        {},
    )

    if normalized_scenario not in scenarios:
        raise KeyError(
            "Escenario inexistente para telemetría: "
            f"{normalized_scenario}"
        )

    complete_result = scenarios[
        normalized_scenario
    ]

    live_result = slice_result_until_time(
        result=complete_result,
        target_time_s=target_time_s,
    )

    live_scenarios = dict(
        scenarios
    )

    live_scenarios[
        normalized_scenario
    ] = live_result

    live_dataset = dict(
        dataset
    )

    live_dataset[
        "scenarios"
    ] = live_scenarios

    live_view = build_scenario_view(
        dataset=live_dataset,
        scenario_name=normalized_scenario,
    )

    return live_view[
        "telemetry"
    ]
def build_live_orbit_figure(
    dataset: Mapping[str, Any],
    scenario_name: str,
    target_time_s: object,
) -> Any:
    """
    Construye la formación orbital 3D para un instante.

    Solo utiliza los snapshots disponibles hasta
    el tiempo actual de la animación.
    """

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    scenarios = dataset.get(
        "scenarios",
        {},
    )

    if normalized_scenario not in scenarios:
        raise KeyError(
            "Escenario inexistente para órbita 3D: "
            f"{normalized_scenario}"
        )

    complete_result = scenarios[
        normalized_scenario
    ]

    live_result = slice_result_until_time(
        result=complete_result,
        target_time_s=target_time_s,
    )

    return build_orbit_3d_figure(
        result=live_result,
        scenario_name=normalized_scenario,
        target_time_s=target_time_s,
    )
def build_live_temporal_figures(
    dataset: Mapping[str, Any],
    scenario_name: str,
    target_time_s: object,
) -> tuple[Any, Any, Any, Any]:
    """
    Construye las cuatro gráficas temporales hasta
    el instante actual de la animación.

    Las figuras muestran únicamente los snapshots
    cuyo tiempo es menor o igual al reloj de misión.
    """

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    scenarios = dataset.get(
        "scenarios",
        {},
    )

    if normalized_scenario not in scenarios:
        raise KeyError(
            "Escenario inexistente para gráficas: "
            f"{normalized_scenario}"
        )

    complete_result = scenarios[
        normalized_scenario
    ]

    live_result = slice_result_until_time(
        result=complete_result,
        target_time_s=target_time_s,
    )

    return build_temporal_figures(
        result=live_result,
        scenario_name=normalized_scenario,
    )
def build_live_event_view(
    dataset: Mapping[str, Any],
    scenario_name: str,
    target_time_s: object,
) -> dict[str, Any]:
    """
    Construye el registro de eventos hasta el reloj actual.
    """

    normalized_scenario = (
        str(scenario_name)
        .strip()
        .upper()
    )

    scenarios = dataset.get(
        "scenarios",
        {},
    )

    if normalized_scenario not in scenarios:
        raise KeyError(
            "Escenario inexistente para eventos: "
            f"{normalized_scenario}"
        )

    result = scenarios[
        normalized_scenario
    ]

    selected_events = (
        slice_events_until_time(
            result=result,
            target_time_s=target_time_s,
        )
    )

    original_events = result.get(
        "events",
        [],
    )

    total_event_count = (
        len(original_events)
        if isinstance(
            original_events,
            list,
        )
        else 0
    )

    current_event_count = len(
        selected_events
    )

    return {
        "events": selected_events,
        "current_count": (
            current_event_count
        ),
        "total_count": (
            total_event_count
        ),
        "count_text": str(
            current_event_count
        ),
        "badge_text": (
            f"{current_event_count}"
            f"/{total_event_count}"
        ),
        "event_feed": build_event_feed(
            selected_events
        ),
    }
def register_callbacks(
    app: Dash,
    dataset: Mapping[str, Any],
):
    """Registra los callbacks del selector."""

    @app.callback(
        [
            Output(
                "kpi-satellite-count",
                "children",
            ),
            Output(
                "kpi-duration",
                "children",
            ),
            Output(
                "kpi-snapshot-count",
                "children",
            ),

            Output(
                "kpi-resilience-score",
                "children",
            ),
            Output(
                "kpi-classification",
                "children",
            ),
            Output(
                "active-scenario",
                "children",
            ),
        
        ],
        Input(
            "scenario-selector",
            "value",
        ),
    )
    def update_selected_scenario(
        scenario_name: str | None,
    ) -> tuple[Any, ...]:
        """Actualiza el escenario seleccionado."""

        if not scenario_name:
            raise PreventUpdate

        try:
            view = build_scenario_view(
                dataset=dataset,
                scenario_name=scenario_name,
            )
        except KeyError as error:
            print(
                "No se pudo actualizar "
                f"el dashboard: {error}"
            )
            raise PreventUpdate from error

        return (
            view["satellite_count"],
            view["duration"],
            view["snapshot_count"],
            view["resilience_score"],
            view["classification"],
            view["active_scenario"],
        )
    
        # ==========================================================
    # CALLBACK 2 — CONTROL TEMPORAL DE LA ANIMACIÓN
    # ==========================================================

    @app.callback(
        [
            Output(
                "animation-state-store",
                "data",
            ),
            Output(
                "dashboard-clock",
                "disabled",
            ),
            Output(
                "button-start",
                "disabled",
            ),
            Output(
                "button-pause",
                "disabled",
            ),
            Output(
                "button-reset",
                "disabled",
            ),
            Output(
                "simulation-time",
                "children",
            ),
            Output(
                "simulation-status",
                "children",
            ),
            Output(
                "telemetry-panel",
                "children",
            ),
            Output(
                "orbit-3d-graph",
                "figure",
            ),
            Output(
                "temporal-figures-store",
                "data",
            ),
            Output(
                "kpi-event-count",
                "children",
            ),
            Output(
                "event-count-badge",
                "children",
            ),
            Output(
                "event-feed",
                "children",
            ),
            Output(
                "mission-progress-bar",
                "style",
            ),
            Output(
                "mission-progress-label",
                "children",
            ),
        ],
        [
            Input(
                "button-start",
                "n_clicks",
            ),
            Input(
                "button-pause",
                "n_clicks",
            ),
            Input(
                "button-reset",
                "n_clicks",
            ),
            Input(
                "dashboard-clock",
                "n_intervals",
            ),
            Input(
                "scenario-selector",
                "value",
            ),
        ],
        State(
            "animation-state-store",
            "data",
        ),
        prevent_initial_call=False,
    )
    def control_animation(
        start_clicks: int | None,
        pause_clicks: int | None,
        reset_clicks: int | None,
        interval_count: int | None,
        scenario_name: str | None,
        animation_state: Mapping[str, Any] | None,
    ) -> tuple[Any, ...]:
        """
        Controla los botones INICIAR, PAUSAR y REINICIAR.

        También avanza el reloj cuando se activa
        el componente dashboard-clock.
        """

        # Estos valores solo permiten que Dash detecte
        # qué componente activó el callback.


        if not scenario_name:
            raise PreventUpdate

        normalized_scenario = (
            str(scenario_name)
            .strip()
            .upper()
        )

        scenarios = dataset.get(
            "scenarios",
            {},
        )

        if normalized_scenario not in scenarios:
            raise PreventUpdate

        result = scenarios[
            normalized_scenario
        ]

        # ======================================================
        # CONTROL ROBUSTO CONTRA PULSOS ATRASADOS DEL INTERVALO
        # ======================================================

        trigger_id = ctx.triggered_id

        # Dash puede informar más de una propiedad disparadora.
        # El selector siempre debe tener prioridad sobre cualquier
        # pulso atrasado del temporizador.
        triggered_prop_ids = getattr(
            ctx,
            "triggered_prop_ids",
            {},
        )

        if isinstance(triggered_prop_ids, Mapping):
            triggered_component_ids = {
                str(component_id)
                for component_id
                in triggered_prop_ids.values()
            }
        else:
            triggered_component_ids = set()

        selector_triggered = (
            trigger_id == "scenario-selector"
            or "scenario-selector"
            in triggered_component_ids
        )

        # Contadores actuales de los botones.
        start_count = int(
            start_clicks or 0
        )

        pause_count = int(
            pause_clicks or 0
        )

        reset_count = int(
            reset_clicks or 0
        )

        # Copia segura del estado recibido.
        current_state = dict(
            animation_state or {}
        )

        # Últimos clics que ya fueron procesados.
        handled_start = int(
            current_state.get(
                "_handled_start_clicks",
                0,
            )
        )

        handled_pause = int(
            current_state.get(
                "_handled_pause_clicks",
                0,
            )
        )

        handled_reset = int(
            current_state.get(
                "_handled_reset_clicks",
                0,
            )
        )

        state_scenario = (
            str(
                current_state.get(
                    "scenario",
                    "",
                )
            )
            .strip()
            .upper()
        )

        # Un pulso del reloj perteneciente al escenario anterior
        # jamás debe sobrescribir la selección nueva del usuario.
        if (
            trigger_id == "dashboard-clock"
            and state_scenario
            and state_scenario != normalized_scenario
        ):
            raise PreventUpdate

        scenario_changed = (
            trigger_id is None
            or selector_triggered
            or state_scenario
            != normalized_scenario
        )

        if selector_triggered:
            print(
                "[G3] Escenario seleccionado: "
                f"{normalized_scenario}"
            )

        # Detecta una pulsación nueva del botón PAUSAR.
        # Esta bandera se utiliza más adelante para congelar
        # todas las figuras sin reconstruirlas.
        pause_requested = (
            trigger_id == "button-pause"
            and pause_count > handled_pause
        )

        # Al cambiar de escenario se reinicia todo.
        if scenario_changed:
            new_state = reset_animation(
                scenario_name=(
                    normalized_scenario
                ),
                result=result,
            )

        # REINICIAR tiene máxima prioridad.
        elif reset_count > handled_reset:
            new_state = reset_animation(
                scenario_name=(
                    normalized_scenario
                ),
                result=result,
            )

        # PAUSAR tiene prioridad sobre cualquier pulso pendiente.
        elif pause_count > handled_pause:
            new_state = pause_animation(
                state=current_state,
                scenario_name=(
                    normalized_scenario
                ),
                result=result,
            )

        # INICIAR se procesa después de pausa y reinicio.
        elif start_count > handled_start:
            new_state = start_animation(
                state=current_state,
                scenario_name=(
                    normalized_scenario
                ),
                result=result,
            )

        # El reloj solo avanza cuando running es verdadero.
        elif trigger_id == "dashboard-clock":
            normalized_state = (
                normalize_animation_state(
                    state=current_state,
                    scenario_name=(
                        normalized_scenario
                    ),
                    result=result,
                )
            )

            if bool(
                normalized_state.get(
                    "running",
                    False,
                )
            ):
                new_state = advance_animation(
                    state=normalized_state,
                    scenario_name=(
                        normalized_scenario
                    ),
                    result=result,
                )
            else:
                # Si está pausado, conserva exactamente
                # el mismo tiempo y las mismas gráficas.
                new_state = normalized_state

        else:
            new_state = normalize_animation_state(
                state=current_state,
                scenario_name=(
                    normalized_scenario
                ),
                result=result,
            )

        # Guarda qué clics ya fueron atendidos.
        # Esto impide que un pulso atrasado ignore PAUSAR.
        new_state = dict(new_state)

        new_state[
            "_handled_start_clicks"
        ] = start_count

        new_state[
            "_handled_pause_clicks"
        ] = pause_count

        new_state[
            "_handled_reset_clicks"
        ] = reset_count

        running = bool(
            new_state.get(
                "running",
                False,
            )
        )

        completed = bool(
            new_state.get(
                "completed",
                False,
            )
        )

        time_count = int(
            new_state.get(
                "time_count",
                0,
            )
        )

        time_index = int(
            new_state.get(
                "time_index",
                0,
            )
        )

        # Estado textual mostrado en el pie
        # del dashboard.
        if completed:
            status_text = (
                "MISIÓN COMPLETADA"
            )

        elif running:
            status_text = (
                "EJECUTANDO"
            )

        elif time_index > 0:
            status_text = (
                "PAUSADO"
            )

        else:
            status_text = (
                "LISTO"
            )

        # El intervalo funciona únicamente cuando
        # la animación está ejecutándose.
        interval_disabled = not running

        # Mientras se ejecuta, no se puede volver
        # a presionar INICIAR.
        start_disabled = (
            running
            or time_count <= 1
        )

        # PAUSAR solo funciona cuando la misión
        # está ejecutándose.
        pause_disabled = not running

        # REINICIAR estará disponible siempre que
        # exista más de un instante temporal.
        reset_disabled = (
            time_count <= 1
        )

        mission_time = format_mission_time(
            new_state.get(
                "time_s",
                0.0,
            )
        )

        # Cuando se pulsa PAUSAR no se reconstruyen las figuras.
        # También se ignora cualquier pulso del intervalo que llegue
        # mientras el estado ya se encuentre detenido.
        freeze_visuals = (
            pause_requested
            or (
                trigger_id == "dashboard-clock"
                and not running
                and not completed
            )
        )  

        if freeze_visuals:
            live_telemetry = no_update
            live_orbit_figure = no_update
            temporal_figures_payload = no_update
            live_event_count = no_update
            live_event_badge = no_update
            live_event_feed = no_update
            progress_style = no_update
            progress_label = no_update

        else:
            live_telemetry = (
                build_live_telemetry_view(
                    dataset=dataset,
                    scenario_name=(
                        normalized_scenario
                    ),
                    target_time_s=(
                        new_state.get(
                            "time_s",
                            0.0,
                        )
                    ),
                )
            )

            live_orbit_figure = (
                build_live_orbit_figure(
                    dataset=dataset,
                    scenario_name=(
                        normalized_scenario
                    ),
                    target_time_s=(
                        new_state.get(
                            "time_s",
                            0.0,
                        )
                    ),
                )
            )

            (
                live_formation_figure,
                live_soc_figure,
                live_link_margin_figure,
                live_isl_availability_figure,
            ) = build_live_temporal_figures(
                dataset=dataset,
                scenario_name=(
                    normalized_scenario
                ),
                target_time_s=(
                    new_state.get(
                        "time_s",
                        0.0,
                    )
                ),
            )

            # Las cuatro figuras viajan en un único paquete atómico.
            # El navegador rechazará cualquier paquete atrasado cuyo
            # escenario no coincida con el selector actual.
            temporal_figures_payload = {
                "scenario": normalized_scenario,
                "formation": (
                    live_formation_figure.to_plotly_json()
                ),
                "soc": (
                    live_soc_figure.to_plotly_json()
                ),
                "link_margin": (
                    live_link_margin_figure.to_plotly_json()
                ),
                "availability": (
                    live_isl_availability_figure.to_plotly_json()
                ),
            }

            live_event_view = (
                build_live_event_view(
                    dataset=dataset,
                    scenario_name=(
                        normalized_scenario
                    ),
                    target_time_s=(
                        new_state.get(
                            "time_s",
                            0.0,
                        )
                    ),
                )
            )

            live_event_count = (
                live_event_view[
                    "count_text"
                ]
            )

            live_event_badge = (
                live_event_view[
                    "badge_text"
                ]
            )

            live_event_feed = (
                live_event_view[
                    "event_feed"
                ]
            )

            # ======================================================
            # PROGRESO BASADO EN EL TIEMPO REAL DE LA MISIÓN
            # ======================================================
        current_time_s = safe_float(
            new_state.get(
               "time_s",
                0.0,
            ),
            default=0.0,
        )

        if current_time_s is None:
            current_time_s = 0.0

        scenario_snapshots = result.get(
            "snapshots",
             [],
        )

        # Obtiene el último tiempo real registrado en los snapshots.
        duration_s = max(
       (
         snapshot_time_s(snapshot)
         for snapshot in scenario_snapshots
         if isinstance(snapshot, Mapping)
        ),
        default=0.0,
        )

        # Se considera completada cuando:
        # 1. El estado de animación indica completed, o
        # 2. El reloj alcanzó el último instante disponible.
        mission_completed = (
           completed
          or (
              duration_s > 0.0
              and current_time_s
              >= duration_s - 1e-9
             )
        )

        if mission_completed:
          progress_percent = 100.0

        elif duration_s > 0.0:
           progress_percent = (
            current_time_s
          / duration_s
          * 100.0
        )

        else:
            progress_percent = 0.0

        progress_percent = max(
           0.0,
           min(
               100.0,
              progress_percent,
            ),
        )

        progress_style = {
           "width": (
              f"{progress_percent:.1f}%"
           ),
       }

        progress_label = (
            f"{progress_percent:.1f} %"
        )

        return (
            new_state,
            interval_disabled,
            start_disabled,
            pause_disabled,
            reset_disabled,
            mission_time,
            status_text,
            live_telemetry,
            live_orbit_figure,
            temporal_figures_payload,
            live_event_count,
            live_event_badge,
            live_event_feed,
            progress_style,
            progress_label,
        )

    # ==========================================================
    # CALLBACK 3 — ENTREGA ATÓMICA DE LAS CUATRO GRÁFICAS
    # ==========================================================
    # Un pulso atrasado puede terminar después de que el usuario
    # cambió de escenario. Este callback se ejecuta en el navegador
    # y descarta cualquier paquete que no corresponda al selector.

    app.clientside_callback(
        """
        function(payload, selectedScenario) {
            const noUpdate = window.dash_clientside.no_update;

            if (!payload || !selectedScenario) {
                return [noUpdate, noUpdate, noUpdate, noUpdate];
            }

            const selected = String(selectedScenario)
                .trim()
                .toUpperCase();
            const received = String(payload.scenario || "")
                .trim()
                .toUpperCase();

            if (!received || received !== selected) {
                console.warn(
                    "[G3] Paquete temporal atrasado descartado:",
                    received,
                    "!=",
                    selected
                );
                return [noUpdate, noUpdate, noUpdate, noUpdate];
            }

            return [
                payload.formation,
                payload.soc,
                payload.link_margin,
                payload.availability
            ];
        }
        """,
        [
            Output(
                "graph-formation-error",
                "figure",
            ),
            Output(
                "graph-soc",
                "figure",
            ),
            Output(
                "graph-link-margin",
                "figure",
            ),
            Output(
                "graph-isl-availability",
                "figure",
            ),
        ],
        [
            Input(
                "temporal-figures-store",
                "data",
            ),
            Input(
                "scenario-selector",
                "value",
            ),
        ],
        prevent_initial_call=False,
    )

    # Esta debe ser la última línea dentro
    # de register_callbacks().
    return update_selected_scenario