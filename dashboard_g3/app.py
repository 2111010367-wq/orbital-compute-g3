"""Aplicación principal del dashboard profesional G3."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dash import Dash

from dashboard_g3.callbacks import (
    register_callbacks,
)

from dashboard_g3.data_loader import (
    build_dashboard_dataset,
)
from dashboard_g3.layout import (
    create_dashboard_layout,
)


PACKAGE_DIRECTORY = Path(
    __file__
).resolve().parent

PROJECT_DIRECTORY = (
    PACKAGE_DIRECTORY.parent
)

SCENARIOS_DIRECTORY = (
    PROJECT_DIRECTORY
    / "resultados"
    / "escenarios_fase15"
)

COMPARISON_JSON = (
    PROJECT_DIRECTORY
    / "resultados"
    / "comparacion_fase15"
    / "comparacion_escenarios.json"
)

ASSESSMENT_JSON = (
    PROJECT_DIRECTORY
    / "resultados"
    / "evaluacion_resiliencia_fase15"
    / "evaluacion_resiliencia.json"
)

ASSETS_DIRECTORY = (
    PACKAGE_DIRECTORY
    / "assets"
)


def load_project_dataset() -> dict[str, Any]:
    """Carga los resultados reales del proyecto."""

    return build_dashboard_dataset(
        scenarios_directory=(
            SCENARIOS_DIRECTORY
        ),
        comparison_json_path=(
            COMPARISON_JSON
        ),
        assessment_json_path=(
            ASSESSMENT_JSON
        ),
    )


def create_app(
    dataset: Mapping[str, Any] | None = None,
) -> Dash:
    """Crea y configura la aplicación Dash."""

    dashboard_dataset = (
        dict(dataset)
        if dataset is not None
        else load_project_dataset()
    )

    app = Dash(
        __name__,
        assets_folder=str(
            ASSETS_DIRECTORY
        ),
        suppress_callback_exceptions=True,
        title=(
            "G3 | Orbital Cognitive "
            "Formation Control"
        ),
        update_title=(
            "Actualizando telemetría..."
        ),
    )

    app.layout = create_dashboard_layout(
    dashboard_dataset
    )

    register_callbacks(
    app=app,
    dataset=dashboard_dataset,
    )

    return app