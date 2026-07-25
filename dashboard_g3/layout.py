"""
Diseño visual principal del dashboard profesional G3.

La interfaz presenta:

- Selector de escenarios.
- Tarjetas KPI.
- Vista orbital 3D preliminar.
- Estado de los tres satélites.
- Registro de eventos.
- Controles preparados para fases posteriores.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dashboard_g3.animation import (
    create_animation_state,
    format_mission_time,
)
from dashboard_g3.figures.orbit_3d import (
    build_orbit_3d_figure,
)

from dashboard_g3.figures.temporal import (
    build_temporal_figures,
)
SCENARIO_LABELS = {
    "NOMINAL": "Operación nominal",
    "LOW_POWER": "Baja disponibilidad energética",
    "ISL_DEGRADATION": "Degradación del enlace ISL",
    "ISL_BLACKOUT": "Interrupción del enlace ISL",
    "SATELLITE_FAILURE": "Falla de satélite",
    "FORMATION_DISTURBANCE": "Perturbación de formación",
    "FEDERATED_EXCLUSION": "Exclusión del aprendizaje federado",
    "COMBINED_FAILURE": "Falla combinada",
}


def first_available(
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
    default: Any = None,
) -> Any:
    """Obtiene el primer campo disponible."""

    for key in keys:
        if key in mapping:
            return mapping[key]

    return default


def format_number(
    value: object,
    decimals: int = 1,
    default: str = "N/D",
) -> str:
    """Formatea un valor numérico."""

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return default


def assessment_score(
    assessment: Mapping[str, Any],
) -> str:
    """Obtiene el índice de resiliencia."""

    value = first_available(
        assessment,
        (
            "score",
            "resilience_score",
            "resilience_index",
            "puntaje",
        ),
    )

    return format_number(
        value,
        decimals=1,
    )


def assessment_level(
    assessment: Mapping[str, Any],
) -> str:
    """Obtiene la clasificación del escenario."""

    value = first_available(
        assessment,
        (
            "classification",
            "level",
            "status",
            "clasificacion",
        ),
        default="NO CLASIFICADO",
    )

    return str(value).strip().upper()


def build_orbit_preview() -> go.Figure:
    """
    Construye la vista orbital preliminar.

    La dinámica basada en los snapshots reales será
    integrada durante la Fase 17.3.
    """

    longitude = np.linspace(
        0.0,
        2.0 * np.pi,
        70,
    )

    latitude = np.linspace(
        -0.5 * np.pi,
        0.5 * np.pi,
        40,
    )

    longitude_grid, latitude_grid = np.meshgrid(
        longitude,
        latitude,
    )

    earth_radius = 1.0

    earth_x = (
        earth_radius
        * np.cos(latitude_grid)
        * np.cos(longitude_grid)
    )

    earth_y = (
        earth_radius
        * np.cos(latitude_grid)
        * np.sin(longitude_grid)
    )

    earth_z = (
        earth_radius
        * np.sin(latitude_grid)
    )

    orbit_angle = np.linspace(
        0.0,
        2.0 * np.pi,
        180,
    )

    orbit_radius = 1.42

    orbit_x = (
        orbit_radius
        * np.cos(orbit_angle)
    )

    orbit_y = (
        orbit_radius
        * np.sin(orbit_angle)
    )

    orbit_z = (
        0.20
        * np.sin(
            orbit_angle * 2.0
        )
    )

    satellite_angles = np.radians(
        [15.0, 27.0, 39.0]
    )

    satellite_x = (
        orbit_radius
        * np.cos(satellite_angles)
    )

    satellite_y = (
        orbit_radius
        * np.sin(satellite_angles)
    )

    satellite_z = (
        0.20
        * np.sin(
            satellite_angles * 2.0
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Surface(
            x=earth_x,
            y=earth_y,
            z=earth_z,
            surfacecolor=earth_z,
            colorscale=[
                [0.0, "#041c36"],
                [0.45, "#064c75"],
                [0.70, "#0987a8"],
                [1.0, "#69d5e7"],
            ],
            showscale=False,
            opacity=0.96,
            hoverinfo="skip",
            name="Tierra",
        )
    )

    figure.add_trace(
        go.Scatter3d(
            x=orbit_x,
            y=orbit_y,
            z=orbit_z,
            mode="lines",
            line={
                "color": "#288bc7",
                "width": 3,
                "dash": "dot",
            },
            hoverinfo="skip",
            name="Órbita de referencia",
        )
    )

    figure.add_trace(
        go.Scatter3d(
            x=satellite_x,
            y=satellite_y,
            z=satellite_z,
            mode="lines+markers+text",
            marker={
                "size": 8,
                "color": [
                    "#5ce1e6",
                    "#64ff9b",
                    "#ffca5c",
                ],
                "line": {
                    "color": "#ffffff",
                    "width": 1,
                },
            },
            line={
                "color": "#5ce1e6",
                "width": 4,
            },
            text=[
                "SAT-000",
                "SAT-001",
                "SAT-002",
            ],
            textposition="top center",
            textfont={
                "color": "#d9f6ff",
                "size": 11,
            },
            hovertemplate=(
                "<b>%{text}</b>"
                "<br>Vista preliminar"
                "<extra></extra>"
            ),
            name="Formación G3",
        )
    )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={
            "l": 0,
            "r": 0,
            "t": 12,
            "b": 0,
        },
        showlegend=False,
        uirevision="orbit-preview-g3",
        scene={
            "bgcolor": "rgba(0,0,0,0)",
            "aspectmode": "cube",
            "xaxis": {
                "visible": False,
                "showbackground": False,
            },
            "yaxis": {
                "visible": False,
                "showbackground": False,
            },
            "zaxis": {
                "visible": False,
                "showbackground": False,
            },
            "camera": {
                "eye": {
                    "x": 1.55,
                    "y": 1.55,
                    "z": 1.05,
                }
            },
            "annotations": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 1.75,
                    "text": (
                        "VISTA PRELIMINAR · "
                        "DINÁMICA REAL EN FASE 17.3"
                    ),
                    "showarrow": False,
                    "font": {
                        "color": "#7e99ad",
                        "size": 10,
                    },
                }
            ],
        },
    )

    return figure


def build_kpi_card(
    title: str,
    value: str,
    subtitle: str,
    component_id: str,
    tone: str,
) -> html.Div:
    """Construye una tarjeta KPI."""

    return html.Div(
        className=(
            f"kpi-card kpi-card-{tone}"
        ),
        children=[
            html.Div(
                title,
                className="kpi-title",
            ),
            html.Div(
                value,
                id=component_id,
                className="kpi-value",
            ),
            html.Div(
                subtitle,
                className="kpi-subtitle",
            ),
        ],
    )


def build_satellite_cards(
    satellite_ids: list[str],
) -> list[html.Div]:
    """Construye las tarjetas de los satélites."""

    cards: list[html.Div] = []

    for index, satellite_id in enumerate(
        satellite_ids
    ):
        role = (
            "Líder de formación"
            if index == 0
            else f"Seguidor {index}"
        )

        cards.append(
            html.Div(
                className="satellite-card",
                children=[
                    html.Div(
                        className="satellite-card-header",
                        children=[
                            html.Div(
                                satellite_id,
                                className=(
                                    "satellite-name"
                                ),
                            ),
                            html.Div(
                                "EN LÍNEA",
                                className=(
                                    "status-badge "
                                    "status-online"
                                ),
                            ),
                        ],
                    ),
                    html.Div(
                        role,
                        className="satellite-role",
                    ),
                    html.Div(
                        className="satellite-mini-grid",
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
                                        "-- %",
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
                                        "Ka",
                                        className=(
                                            "mini-label"
                                        ),
                                    ),
                                    html.Strong(
                                        "-- dB",
                                        id=(
                                            f"satellite-{index}"
                                            "-margin"
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


def event_description(
    event: Mapping[str, Any],
) -> tuple[str, str, str]:
    """Extrae los datos visibles de un evento."""

    time_value = first_available(
        event,
        (
            "time_s",
            "start_s",
            "timestamp_s",
            "simulation_time_s",
        ),
    )

    try:
        time_text = (
            f"T+{float(time_value) / 60.0:.1f} min"
        )
    except (TypeError, ValueError):
        time_text = "Tiempo no registrado"

    category = str(
        first_available(
            event,
            (
                "event_type",
                "type",
                "category",
                "kind",
            ),
            default="EVENTO",
        )
    ).upper()

    description = str(
        first_available(
            event,
            (
                "description",
                "message",
                "action",
                "reason",
                "name",
            ),
            default="Evento registrado por el simulador.",
        )
    )

    return (
        time_text,
        category,
        description,
    )


def build_event_feed(
    events: list[Any],
) -> list[html.Div]:
    """Construye el registro inicial de eventos."""

    normalized_events = [
        event
        for event in events
        if isinstance(
            event,
            Mapping,
        )
    ]

    if not normalized_events:
        return [
            html.Div(
                className="empty-state",
                children=(
                    "No existen eventos registrados "
                    "para este escenario."
                ),
            )
        ]

    feed: list[html.Div] = []

    for event in normalized_events[-6:]:
        time_text, category, description = (
            event_description(
                event
            )
        )

        feed.append(
            html.Div(
                className="event-row",
                children=[
                    html.Div(
                        className="event-indicator",
                    ),
                    html.Div(
                        className="event-content",
                        children=[
                            html.Div(
                                [
                                    html.Span(
                                        category,
                                        className=(
                                            "event-category"
                                        ),
                                    ),
                                    html.Span(
                                        time_text,
                                        className=(
                                            "event-time"
                                        ),
                                    ),
                                ],
                                className=(
                                    "event-row-header"
                                ),
                            ),
                            html.Div(
                                description,
                                className=(
                                    "event-description"
                                ),
                            ),
                        ],
                    ),
                ],
            )
        )

    return feed


def create_dashboard_layout(
    dataset: Mapping[str, Any],
) -> html.Div:
    """Construye el dashboard completo."""

    scenario_order = list(
        dataset["scenario_order"]
    )

    initial_scenario = (
        "NOMINAL"
        if "NOMINAL" in scenario_order
        else scenario_order[0]
    )

    summary = dataset[
        "scenario_summaries"
    ][initial_scenario]

    assessment = dataset[
        "assessment"
    ][initial_scenario]

    initial_result = dataset[
        "scenarios"
    ][initial_scenario]
    initial_animation_state = (
        create_animation_state(
            scenario_name=initial_scenario,
            result=initial_result,
        )
    )
    initial_orbit_figure = build_orbit_3d_figure(
        result=initial_result,
        scenario_name=initial_scenario,
    )
     
    (
        initial_formation_figure,
        initial_soc_figure,
        initial_margin_figure,
        initial_availability_figure,
    ) = build_temporal_figures(
        result=initial_result,
        scenario_name=initial_scenario,
    )

    satellite_ids = list(
        summary.get(
            "satellite_ids",
            [
                "SAT-000",
                "SAT-001",
                "SAT-002",
            ],
        )
    )

    if not satellite_ids:
        satellite_ids = [
            "SAT-000",
            "SAT-001",
            "SAT-002",
        ]

    return html.Div(
        className="dashboard-shell",
        children=[
            dcc.Store(
                id="dashboard-metadata-store",
                data={
                    "scenario_order": (
                        scenario_order
                    ),
                    "initial_scenario": (
                        initial_scenario
                    ),
                },
            ),
            dcc.Store(
                id="animation-state-store",
                storage_type="memory",
                data=initial_animation_state,
            ),
            dcc.Store(
                id="temporal-figures-store",
                storage_type="memory",
                data=None,
            ),
            dcc.Interval(
                id="dashboard-clock",
                interval=1000,
                n_intervals=0,
                disabled=True,
            ),
            html.Header(
                className="top-header",
                children=[
                    html.Div(
                        className="brand-block",
                        children=[
                            html.Div(
                                "G3",
                                className="brand-emblem",
                            ),
                            html.Div(
                                [
                                    html.H1(
                                        "ORBITAL COGNITIVE "
                                        "FORMATION CONTROL"
                                    ),
                                    html.P(
                                        "Arquitectura cognitiva "
                                        "distribuida para satélites "
                                        "autónomos"
                                    ),
                                ]
                            ),
                        ],
                    ),
                    html.Div(
                        className="mission-state",
                        children=[
                            html.Span(
                                className="live-dot",
                            ),
                            html.Div(
                                [
                                    html.Strong(
                                        "SISTEMA OPERATIVO"
                                    ),
                                    html.Span(
                                        "FASE 17 · G3"
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="control-bar",
                children=[
                    html.Div(
                        className="control-field",
                        children=[
                            html.Label(
                                "ESCENARIO DE MISIÓN"
                            ),
                            dcc.Dropdown(
                                id="scenario-selector",
                                options=[
                                    {
                                        "label": (
                                            SCENARIO_LABELS.get(
                                                scenario,
                                                scenario,
                                            )
                                        ),
                                        "value": scenario,
                                    }
                                    for scenario
                                    in scenario_order
                                ],
                                value=initial_scenario,
                                clearable=False,
                                searchable=False,
                                # El escenario no se conserva en la sesión.
                                # Así el navegador no restaura una selección
                                # antigua después de reiniciar el servidor.
                                persistence=False,
                                className=(
                                    "scenario-dropdown"
                                ),
                            ),
                        ],
                    ),
                    html.Div(
                        className="simulation-controls",
                        children=[
                            html.Button(
                                "▶ INICIAR",
                                id="button-start",
                                n_clicks=0,
                                disabled=False,
                                className=(
                                    "control-button start-button"
                                ),
                                title=(
                                    "Se habilitará en "
                                    "la Fase 17.4"
                                ),
                            ),
                            html.Button(
                                "Ⅱ PAUSAR",
                                id="button-pause",
                                n_clicks=0,
                                disabled=True,
                                className=(
                                    "control-button pause-button"
                                ),
                                title=(
                                    "Se habilitará en "
                                    "la Fase 17.4"
                                ),
                            ),
                            html.Button(
                                "↻ REINICIAR",
                                id="button-reset",
                                n_clicks=0,
                                disabled=False,
                                className=(
                                    "control-button reset-button"
                                ),
                                title=(
                                    "Se habilitará en "
                                    "la Fase 17.4"
                                ),
                            ),
                        ],
                    ),
                html.Div(
                format_mission_time(
                initial_animation_state[
                "time_s"
                     ]
                    ),
                 id="simulation-time",
                 className="simulation-time-value",
                 ),
                html.Div(
                     className="mission-progress-container",
                     children=[
                  html.Div(
                     className="mission-progress-heading",
                     children=[
                     html.Span(
                       "PROGRESO DE MISIÓN",
                     ),
                      html.Span(
                       "0.0 %",
                      id=(
                        "mission-progress-label"
                      ),
                    ),
                 ],
                ),
                html.Div(
                         className=(
                         "mission-progress-track"
                         ),
                        children=[
                        html.Div(
                        id=(
                        "mission-progress-bar"
                        ),
                        className=(
                        "mission-progress-fill"
                        ),
                        style={
                        "width": "0%",
                       },
                    ),
                ],
            ),
        ],
       ), 
                ],
            ),
            html.Main(
                className="dashboard-main",
                children=[
                    html.Section(
                        className="kpi-grid",
                        children=[
                            build_kpi_card(
                                title="SATÉLITES",
                                value=str(
                                    summary[
                                        "satellite_count"
                                    ]
                                ),
                                subtitle=(
                                    "nodos de formación"
                                ),
                                component_id=(
                                    "kpi-satellite-count"
                                ),
                                tone="cyan",
                            ),
                            build_kpi_card(
                                title="DURACIÓN",
                                value=(
                                    format_number(
                                        summary[
                                            "duration_min"
                                        ],
                                        decimals=1,
                                    )
                                ),
                                subtitle="minutos simulados",
                                component_id=(
                                    "kpi-duration"
                                ),
                                tone="blue",
                            ),
                            build_kpi_card(
                                title="SNAPSHOTS",
                                value=str(
                                    summary[
                                        "snapshot_count"
                                    ]
                                ),
                                subtitle=(
                                    "muestras registradas"
                                ),
                                component_id=(
                                    "kpi-snapshot-count"
                                ),
                                tone="violet",
                            ),
                            build_kpi_card(
                                title="EVENTOS",
                                value=str(
                                    summary[
                                        "event_count"
                                    ]
                                ),
                                subtitle=(
                                    "decisiones y fallas"
                                ),
                                component_id=(
                                    "kpi-event-count"
                                ),
                                tone="amber",
                            ),
                            build_kpi_card(
                                title="RESILIENCIA",
                                value=(
                                    assessment_score(
                                        assessment
                                    )
                                ),
                                subtitle="índice sobre 100",
                                component_id=(
                                    "kpi-resilience-score"
                                ),
                                tone="green",
                            ),
                            build_kpi_card(
                                title="CLASIFICACIÓN",
                                value=(
                                    assessment_level(
                                        assessment
                                    )
                                ),
                                subtitle="estado operacional",
                                component_id=(
                                    "kpi-classification"
                                ),
                                tone="status",
                            ),
                        ],
                    ),
                    html.Section(
                        className="content-grid",
                        children=[
                            html.Article(
                                className=(
                                    "dashboard-panel "
                                    "orbit-panel"
                                ),
                                children=[
                                    html.Div(
                                        className=(
                                            "panel-header"
                                        ),
                                        children=[
                                            html.Div(
                                                [
                                                    html.H2(
                                                        "ENTORNO "
                                                        "ORBITAL 3D"
                                                    ),
                                                    html.P(
                                                        "Formación, "
                                                        "órbita e "
                                                        "interconexión "
                                                        "ISL"
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                "DATOS REALES",
                                                className=(
                                                        "panel-tag "
                                                        "panel-tag-green"
                                                ),
                                            ),
                                        ],
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        children=[
                                            dcc.Graph(
                                                id=(
                                                    "orbit-3d-graph"
                                                ),
                                                figure=initial_orbit_figure,
                                                config={
                                                    "displaylogo": (
                                                        False
                                                    ),
                                                    "responsive": (
                                                        True
                                                    ),
                                                    "scrollZoom": (
                                                        True
                                                    ),
                                                },
                                                className=(
                                                    "orbit-graph"
                                                ),
                                            )
                                        ],
                                    ),
                                ],
                            ),
                            html.Aside(
                                className=(
                                    "dashboard-panel "
                                    "satellite-panel"
                                ),
                                children=[
                                    html.Div(
                                        className=(
                                            "panel-header"
                                        ),
                                        children=[
                                            html.Div(
                                                [
                                                    html.H2(
                                                        "TELEMETRÍA"
                                                    ),
                                                    html.P(
                                                        "Estado de "
                                                        "la formación"
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                "3 NODOS",
                                                className=(
                                                    "panel-tag "
                                                    "panel-tag-green"
                                                ),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="telemetry-panel",
                                        className=(
                                            "satellite-list"
                                        ),
                                        children=(
                                            build_satellite_cards(
                                                satellite_ids
                                            )
                                        ),
                                    ),
                                ],
                            ),
                            html.Article(
                                className=(
                                    "dashboard-panel "
                                    "timeline-panel"
                                ),
                                children=[
                                    html.Div(
                                        className=(
                                            "panel-header"
                                        ),
                                        children=[
                                            html.Div(
                                                [
                                                    html.H2(
                                                        "INDICADORES "
                                                        "DE MISIÓN"
                                                    ),
                                                    html.P(
                                                        "Energía, RF, "
                                                        "formación y "
                                                        "FedAvg"
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                initial_scenario,
                                                id=(
                                                    "active-scenario"
                                                ),
                                                className=(
                                                    "panel-tag"
                                                ),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="mission-capabilities",
                                        className="mission-capabilities",
                                        children=[
                                          html.Div(
                                           className="mission-capability",
                                            children=[
                                               html.Span(
                                                "CONTROL",
                                                className="mission-capability-label",
                                                ),
                                               html.Strong(
                                                  "Formación relativa",
                                                   className="mission-capability-value",
                                                ),
                                              ],
                                             ),
                                    html.Div(
                                         className="mission-capability",
                                         children=[
                                              html.Span(
                                                "ENERGÍA",
                                                className="mission-capability-label",
                                               ),
                                               html.Strong(
                                               "Gestión autónoma",
                                               className="mission-capability-value",
                                               ),
                                            ],
                                           ),
                                    html.Div(
                                        className="mission-capability",
                                          children=[
                                         html.Span(
                                         "COMUNICACIÓN",
                                       className="mission-capability-label",
                                        ),
                                        html.Strong(
                                       "Enlace ISL Ka",
                                         className="mission-capability-value",
                                        ),
                                         ],
                                     ),
                                    html.Div(
                                       className="mission-capability",
                                       children=[
                                        html.Span(
                                            "INTELIGENCIA",
                                           className="mission-capability-label",
                                        ),
                                        html.Strong(
                                           "IA federada",
                                            className="mission-capability-value",
                                        ),
                                       ],
                                     ),
                                    ],
                                    ), 
                                ],
                            ),
                            html.Article(
                                className=(
                                    "dashboard-panel "
                                    "events-panel"
                                ),
                                children=[
                                    html.Div(
                                        className=(
                                            "panel-header"
                                        ),
                                        children=[
                                            html.Div(
                                                [
                                                    html.H2(
                                                        "EVENTOS "
                                                        "COGNITIVOS"
                                                    ),
                                                    html.P(
                                                        "Supervisor, "
                                                        "fallas y "
                                                        "decisiones"
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                str(
                                                    summary[
                                                        "event_count"
                                                    ]
                                                ),
                                                id=(
                                                    "event-count-badge"
                                                ),
                                                className=(
                                                    "panel-tag "
                                                    "panel-tag-amber"
                                                ),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="event-feed",
                                        className="event-feed",
                                        children=(
                                            build_event_feed(
                                                initial_result[
                                                    "events"
                                                ]
                                            )
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Section(
                        id="temporal-analysis-section",
                        className="dashboard-section temporal-section",
                        children=[
                            html.Div(
                                className="section-heading",
                                children=[
                                    html.Div(
                                        children=[
                                            html.P(
                                                "ANÁLISIS DINÁMICO",
                                                className="eyebrow",
                                            ),
                                            html.H2(
                                                "Evolución temporal "
                                                "del sistema distribuido"
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        "Datos reales del escenario",
                                        className="section-badge",
                                    ),
                                ],
                            ),
                            html.Div(
                                id="temporal-graphs-grid",
                                className="temporal-graphs-grid",
                                children=[
                                    dcc.Loading(
                                        type="circle",
                                        color="#38bdf8",
                                        children=dcc.Graph(
                                            id="graph-formation-error",
                                            figure=initial_formation_figure,
                                            config={
                                                "displaylogo": False,
                                                "responsive": True,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "lasso2d",
                                                    "select2d",
                                                ],
                                            },
                                        ),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#38bdf8",
                                        children=dcc.Graph(
                                            id="graph-soc",
                                            figure=initial_soc_figure,
                                            config={
                                                "displaylogo": False,
                                                "responsive": True,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "lasso2d",
                                                    "select2d",
                                                ],
                                            },
                                        ),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#38bdf8",
                                        children=dcc.Graph(
                                            id="graph-link-margin",
                                            figure=initial_margin_figure,
                                            config={
                                                "displaylogo": False,
                                                "responsive": True,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "lasso2d",
                                                    "select2d",
                                                ],
                                            },
                                        ),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#38bdf8",
                                        children=dcc.Graph(
                                            id="graph-isl-availability",
                                            figure=initial_availability_figure,
                                            config={
                                                "displaylogo": False,
                                                "responsive": True,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "lasso2d",
                                                    "select2d",
                                                ],
                                            },
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Footer(
                className="dashboard-footer",
                children=[
                    html.Span(
                        "ORBITAL-COMPUTE G3"
                    ),
                    html.Span(
                        "CONTROL DISTRIBUIDO · "
                        "BANDA Ka · IA FEDERADA"
                    ),
                    html.Span(
                        className="footer-status",
                        children=[
                            "ESTADO: ",
                            html.Strong(
                                "LISTO",
                                id="simulation-status",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )