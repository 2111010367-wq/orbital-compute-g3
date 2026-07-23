"""
Visualización profesional de resultados del proyecto G3.

Este módulo carga los resultados comparativos de la Fase 15
y genera figuras exportables en PNG, SVG y PDF.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


EXPORT_FORMATS = (
    "png",
    "svg",
    "pdf",
)


COMPARISON_REQUIRED_FIELDS = {
    "scenario",
    "maximum_final_error_m",
    "minimum_soc_percent",
    "minimum_margin_db",
    "link_availability_percent",
    "node_availability_percent",
    "federated_completion_percent",
    "final_accuracy_percent",
}


ASSESSMENT_REQUIRED_FIELDS = {
    "scenario",
    "score",
    "level",
}


def _read_csv(
    path: str | Path,
) -> list[dict[str, str]]:
    """Lee un archivo CSV UTF-8."""

    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {csv_path}"
        )

    with csv_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        rows = list(reader)

    if not rows:
        raise ValueError(
            f"El archivo está vacío: {csv_path}"
        )

    return rows


def _validate_fields(
    row: Mapping[str, Any],
    required_fields: set[str],
    source_name: str,
) -> None:
    """Comprueba las columnas obligatorias."""

    missing_fields = (
        required_fields
        - set(row)
    )

    if missing_fields:
        raise ValueError(
            f"{source_name} no contiene las columnas: "
            f"{sorted(missing_fields)}"
        )


def load_comparison_rows(
    path: str | Path,
) -> list[dict[str, Any]]:
    """Carga la comparación numérica de escenarios."""

    raw_rows = _read_csv(path)

    rows: list[dict[str, Any]] = []

    for raw_row in raw_rows:
        _validate_fields(
            row=raw_row,
            required_fields=(
                COMPARISON_REQUIRED_FIELDS
            ),
            source_name="Comparación de escenarios",
        )

        rows.append(
            {
                "scenario": raw_row["scenario"],
                "maximum_final_error_m": float(
                    raw_row[
                        "maximum_final_error_m"
                    ]
                ),
                "minimum_soc_percent": float(
                    raw_row[
                        "minimum_soc_percent"
                    ]
                ),
                "minimum_margin_db": float(
                    raw_row[
                        "minimum_margin_db"
                    ]
                ),
                "link_availability_percent": float(
                    raw_row[
                        "link_availability_percent"
                    ]
                ),
                "node_availability_percent": float(
                    raw_row[
                        "node_availability_percent"
                    ]
                ),
                "federated_completion_percent": float(
                    raw_row[
                        "federated_completion_percent"
                    ]
                ),
                "final_accuracy_percent": float(
                    raw_row[
                        "final_accuracy_percent"
                    ]
                ),
            }
        )

    return rows


def load_assessment_rows(
    path: str | Path,
) -> list[dict[str, Any]]:
    """Carga la evaluación de resiliencia."""

    raw_rows = _read_csv(path)

    rows: list[dict[str, Any]] = []

    for raw_row in raw_rows:
        _validate_fields(
            row=raw_row,
            required_fields=(
                ASSESSMENT_REQUIRED_FIELDS
            ),
            source_name=(
                "Evaluación de resiliencia"
            ),
        )

        rows.append(
            {
                "scenario": raw_row["scenario"],
                "score": float(
                    raw_row["score"]
                ),
                "level": raw_row["level"],
            }
        )

    return rows


def save_figure_bundle(
    figure: plt.Figure,
    output_directory: str | Path,
    filename_stem: str,
) -> dict[str, Path]:
    """Guarda una figura en PNG, SVG y PDF."""

    directory = Path(output_directory)

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_files: dict[str, Path] = {}

    for file_format in EXPORT_FORMATS:
        output_path = (
            directory
            / f"{filename_stem}.{file_format}"
        )

        save_arguments: dict[str, Any] = {
            "bbox_inches": "tight",
        }

        if file_format == "png":
            save_arguments["dpi"] = 220

        figure.savefig(
            output_path,
            **save_arguments,
        )

        generated_files[
            file_format
        ] = output_path

    plt.close(figure)

    return generated_files


def plot_resilience_ranking(
    assessment_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera el ranking de resiliencia."""

    if not assessment_rows:
        raise ValueError(
            "No existen evaluaciones "
            "para graficar"
        )

    ordered_rows = sorted(
        assessment_rows,
        key=lambda row: float(
            row["score"]
        ),
    )

    scenarios = [
        str(row["scenario"])
        for row in ordered_rows
    ]

    scores = [
        float(row["score"])
        for row in ordered_rows
    ]

    figure, axis = plt.subplots(
        figsize=(11, 6.5)
    )

    bars = axis.barh(
        scenarios,
        scores,
    )

    axis.set_title(
        "Ranking de resiliencia de los escenarios G3"
    )

    axis.set_xlabel(
        "Índice de resiliencia [0–100]"
    )

    axis.set_ylabel(
        "Escenario"
    )

    axis.set_xlim(
        0.0,
        105.0,
    )

    axis.grid(
        axis="x",
        alpha=0.30,
    )

    for bar, score in zip(
        bars,
        scores,
    ):
        axis.text(
            score + 1.0,
            bar.get_y()
            + bar.get_height() / 2.0,
            f"{score:.2f}",
            va="center",
        )

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "01_ranking_resiliencia"
        ),
    )


def plot_final_formation_error(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica el error final máximo de formación."""

    scenarios = [
        str(row["scenario"])
        for row in comparison_rows
    ]

    errors = [
        float(
            row[
                "maximum_final_error_m"
            ]
        )
        for row in comparison_rows
    ]

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    bars = axis.bar(
        scenarios,
        errors,
    )

    axis.set_title(
        "Error final máximo de formación"
    )

    axis.set_xlabel(
        "Escenario"
    )

    axis.set_ylabel(
        "Error de formación [m]"
    )

    axis.tick_params(
        axis="x",
        rotation=30,
    )

    axis.grid(
        axis="y",
        alpha=0.30,
    )

    for bar, value in zip(
        bars,
        errors,
    ):
        axis.text(
            bar.get_x()
            + bar.get_width() / 2.0,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
        )

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "02_error_final_formacion"
        ),
    )


def plot_minimum_soc(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica el estado mínimo de carga."""

    scenarios = [
        str(row["scenario"])
        for row in comparison_rows
    ]

    minimum_soc = [
        float(
            row[
                "minimum_soc_percent"
            ]
        )
        for row in comparison_rows
    ]

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    bars = axis.bar(
        scenarios,
        minimum_soc,
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

    axis.set_title(
        "Estado mínimo de carga por escenario"
    )

    axis.set_xlabel(
        "Escenario"
    )

    axis.set_ylabel(
        "SOC mínimo [%]"
    )

    axis.tick_params(
        axis="x",
        rotation=30,
    )

    axis.grid(
        axis="y",
        alpha=0.30,
    )

    axis.legend()

    for bar, value in zip(
        bars,
        minimum_soc,
    ):
        axis.text(
            bar.get_x()
            + bar.get_width() / 2.0,
            value,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "03_soc_minimo"
        ),
    )


def plot_minimum_link_margin(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica el margen mínimo del enlace Ka."""

    scenarios = [
        str(row["scenario"])
        for row in comparison_rows
    ]

    margins = [
        float(
            row[
                "minimum_margin_db"
            ]
        )
        for row in comparison_rows
    ]

    figure, axis = plt.subplots(
        figsize=(12, 6.5)
    )

    bars = axis.bar(
        scenarios,
        margins,
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

    axis.set_title(
        "Margen mínimo del enlace intersatelital Ka"
    )

    axis.set_xlabel(
        "Escenario"
    )

    axis.set_ylabel(
        "Margen mínimo [dB]"
    )

    axis.tick_params(
        axis="x",
        rotation=30,
    )

    axis.grid(
        axis="y",
        alpha=0.30,
    )

    axis.legend()

    for bar, value in zip(
        bars,
        margins,
    ):
        axis.text(
            bar.get_x()
            + bar.get_width() / 2.0,
            value,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "04_margen_minimo_ka"
        ),
    )


def generate_phase16_summary_charts(
    comparison_csv_path: str | Path,
    assessment_csv_path: str | Path,
    output_directory: str | Path,
) -> dict[
    str,
    dict[str, Path],
]:
    """Genera el primer paquete gráfico de la Fase 16."""

    comparison_rows = load_comparison_rows(
        comparison_csv_path
    )

    assessment_rows = load_assessment_rows(
        assessment_csv_path
    )

    return {
        "resilience_ranking": (
            plot_resilience_ranking(
                assessment_rows=(
                    assessment_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "formation_error": (
            plot_final_formation_error(
                comparison_rows=(
                    comparison_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "minimum_soc": (
            plot_minimum_soc(
                comparison_rows=(
                    comparison_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "minimum_link_margin": (
            plot_minimum_link_margin(
                comparison_rows=(
                    comparison_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
    }