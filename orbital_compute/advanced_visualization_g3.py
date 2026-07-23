"""
Visualización comparativa avanzada del proyecto G3.

Genera:

- Matriz de calor operacional.
- Radar multidominio.
- Comparación de disponibilidad y FedAvg.
- Mapa de criticidad y resiliencia.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from orbital_compute.visualization_results_g3 import (
    load_assessment_rows,
    load_comparison_rows,
    save_figure_bundle,
)


HEALTH_METRIC_NAMES = (
    "Formación",
    "Energía",
    "Margen Ka",
    "ISL",
    "Nodos",
    "FedAvg",
    "Exactitud",
)


def clamp_percentage(
    value: float,
) -> float:
    """Limita un indicador al intervalo [0, 100]."""

    return max(
        0.0,
        min(
            100.0,
            float(value),
        ),
    )


def find_nominal_row(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
) -> Mapping[str, Any]:
    """Localiza el escenario nominal."""

    nominal = next(
        (
            row
            for row in comparison_rows
            if str(row["scenario"]) == "NOMINAL"
        ),
        None,
    )

    if nominal is None:
        raise ValueError(
            "No existe el escenario NOMINAL"
        )

    return nominal


def scenario_health_vector(
    row: Mapping[str, Any],
    nominal_row: Mapping[str, Any],
) -> list[float]:
    """
    Convierte las métricas del escenario en indicadores
    de salud operacional entre 0 y 100.
    """

    formation_error = float(
        row["maximum_final_error_m"]
    )

    formation_health = (
        100.0
        * (
            1.0
            - formation_error / 1.0
        )
    )

    nominal_soc = float(
        nominal_row["minimum_soc_percent"]
    )

    if nominal_soc > 0.0:
        energy_health = (
            float(
                row["minimum_soc_percent"]
            )
            / nominal_soc
            * 100.0
        )
    else:
        energy_health = 0.0

    nominal_margin = float(
        nominal_row["minimum_margin_db"]
    )

    if nominal_margin > 0.0:
        rf_health = (
            float(
                row["minimum_margin_db"]
            )
            / nominal_margin
            * 100.0
        )
    else:
        rf_health = 0.0

    nominal_federated = float(
        nominal_row[
            "federated_completion_percent"
        ]
    )

    if nominal_federated > 0.0:
        federated_health = (
            float(
                row[
                    "federated_completion_percent"
                ]
            )
            / nominal_federated
            * 100.0
        )
    else:
        federated_health = 0.0

    nominal_accuracy = float(
        nominal_row[
            "final_accuracy_percent"
        ]
    )

    if nominal_accuracy > 0.0:
        accuracy_health = (
            float(
                row[
                    "final_accuracy_percent"
                ]
            )
            / nominal_accuracy
            * 100.0
        )
    else:
        accuracy_health = 0.0

    return [
        clamp_percentage(
            formation_health
        ),
        clamp_percentage(
            energy_health
        ),
        clamp_percentage(
            rf_health
        ),
        clamp_percentage(
            float(
                row[
                    "link_availability_percent"
                ]
            )
        ),
        clamp_percentage(
            float(
                row[
                    "node_availability_percent"
                ]
            )
        ),
        clamp_percentage(
            federated_health
        ),
        clamp_percentage(
            accuracy_health
        ),
    ]


def build_health_matrix(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
) -> tuple[
    list[str],
    list[str],
    np.ndarray,
]:
    """Construye la matriz normalizada de salud."""

    if not comparison_rows:
        raise ValueError(
            "No existen escenarios para comparar"
        )

    nominal_row = find_nominal_row(
        comparison_rows
    )

    scenarios = [
        str(row["scenario"])
        for row in comparison_rows
    ]

    matrix = np.asarray(
        [
            scenario_health_vector(
                row=row,
                nominal_row=nominal_row,
            )
            for row in comparison_rows
        ],
        dtype=float,
    )

    return (
        scenarios,
        list(HEALTH_METRIC_NAMES),
        matrix,
    )


def plot_operational_heatmap(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera una matriz de calor de salud operacional."""

    scenarios, metrics, matrix = (
        build_health_matrix(
            comparison_rows
        )
    )

    figure, axis = plt.subplots(
        figsize=(12.5, 7.0)
    )

    image = axis.imshow(
        matrix,
        aspect="auto",
        vmin=0.0,
        vmax=100.0,
        cmap="viridis",
    )

    axis.set_title(
        "Matriz de salud operacional de los escenarios G3"
    )

    axis.set_xlabel(
        "Dominio operacional"
    )

    axis.set_ylabel(
        "Escenario"
    )

    axis.set_xticks(
        np.arange(
            len(metrics)
        ),
        labels=metrics,
        rotation=25,
        ha="right",
    )

    axis.set_yticks(
        np.arange(
            len(scenarios)
        ),
        labels=scenarios,
    )

    for row_index in range(
        matrix.shape[0]
    ):
        for column_index in range(
            matrix.shape[1]
        ):
            value = matrix[
                row_index,
                column_index,
            ]

            axis.text(
                column_index,
                row_index,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=8,
            )

    colorbar = figure.colorbar(
        image,
        ax=axis,
    )

    colorbar.set_label(
        "Índice de salud [0–100]"
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "01_matriz_calor_operacional"
        ),
    )


def select_radar_scenarios(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    assessment_rows: Sequence[
        Mapping[str, Any]
    ],
) -> list[str]:
    """Selecciona nominal y los tres escenarios más críticos."""

    score_by_scenario = {
        str(row["scenario"]): float(
            row["score"]
        )
        for row in assessment_rows
    }

    failure_scenarios = [
        str(row["scenario"])
        for row in comparison_rows
        if str(row["scenario"]) != "NOMINAL"
    ]

    ordered_failures = sorted(
        failure_scenarios,
        key=lambda scenario: (
            score_by_scenario.get(
                scenario,
                100.0,
            )
        ),
    )

    return [
        "NOMINAL",
        *ordered_failures[:3],
    ]


def plot_multidomain_radar(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    assessment_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera un radar multidominio."""

    nominal_row = find_nominal_row(
        comparison_rows
    )

    row_by_scenario = {
        str(row["scenario"]): row
        for row in comparison_rows
    }

    selected_scenarios = (
        select_radar_scenarios(
            comparison_rows=(
                comparison_rows
            ),
            assessment_rows=(
                assessment_rows
            ),
        )
    )

    metric_count = len(
        HEALTH_METRIC_NAMES
    )

    angles = np.linspace(
        0.0,
        2.0 * np.pi,
        metric_count,
        endpoint=False,
    ).tolist()

    closed_angles = (
        angles
        + angles[:1]
    )

    figure, axis = plt.subplots(
        figsize=(9.5, 8.0),
        subplot_kw={
            "projection": "polar"
        },
    )

    for scenario in selected_scenarios:
        row = row_by_scenario[
            scenario
        ]

        values = scenario_health_vector(
            row=row,
            nominal_row=nominal_row,
        )

        closed_values = (
            values
            + values[:1]
        )

        axis.plot(
            closed_angles,
            closed_values,
            linewidth=2.0,
            label=scenario,
        )

        axis.fill(
            closed_angles,
            closed_values,
            alpha=0.08,
        )

    axis.set_title(
        "Radar multidominio de resiliencia operacional",
        pad=25,
    )

    axis.set_xticks(
        angles,
        labels=HEALTH_METRIC_NAMES,
    )

    axis.set_ylim(
        0.0,
        100.0,
    )

    axis.set_yticks(
        [
            20.0,
            40.0,
            60.0,
            80.0,
            100.0,
        ]
    )

    axis.grid(
        alpha=0.35,
    )

    axis.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.35,
            1.15,
        ),
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "02_radar_multidominio"
        ),
    )


def plot_availability_and_federated(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Compara ISL, nodos y FedAvg."""

    scenarios = [
        str(row["scenario"])
        for row in comparison_rows
    ]

    link_availability = [
        float(
            row[
                "link_availability_percent"
            ]
        )
        for row in comparison_rows
    ]

    node_availability = [
        float(
            row[
                "node_availability_percent"
            ]
        )
        for row in comparison_rows
    ]

    federated_completion = [
        float(
            row[
                "federated_completion_percent"
            ]
        )
        for row in comparison_rows
    ]

    positions = np.arange(
        len(scenarios)
    )

    bar_width = 0.25

    figure, axis = plt.subplots(
        figsize=(13.0, 7.0)
    )

    axis.bar(
        positions - bar_width,
        link_availability,
        width=bar_width,
        label="Disponibilidad ISL",
    )

    axis.bar(
        positions,
        node_availability,
        width=bar_width,
        label="Disponibilidad de nodos",
    )

    axis.bar(
        positions + bar_width,
        federated_completion,
        width=bar_width,
        label="Rondas FedAvg completadas",
    )

    axis.axhline(
        90.0,
        linestyle="--",
        linewidth=1.0,
        label="Referencia operacional: 90 %",
    )

    axis.set_title(
        "Disponibilidad y continuidad del aprendizaje federado"
    )

    axis.set_xlabel(
        "Escenario"
    )

    axis.set_ylabel(
        "Indicador [%]"
    )

    axis.set_ylim(
        0.0,
        110.0,
    )

    axis.set_xticks(
        positions,
        labels=scenarios,
        rotation=30,
        ha="right",
    )

    axis.grid(
        axis="y",
        alpha=0.30,
    )

    axis.legend(
        loc="lower left",
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "03_disponibilidad_y_fedavg"
        ),
    )


def plot_resilience_criticality_map(
    comparison_rows: Sequence[
        Mapping[str, Any]
    ],
    assessment_rows: Sequence[
        Mapping[str, Any]
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera el mapa de criticidad de escenarios."""

    comparison_by_scenario = {
        str(row["scenario"]): row
        for row in comparison_rows
    }

    scenarios: list[str] = []
    resilience_scores: list[float] = []
    formation_errors: list[float] = []
    bubble_sizes: list[float] = []

    for assessment in assessment_rows:
        scenario = str(
            assessment["scenario"]
        )

        if scenario not in comparison_by_scenario:
            continue

        comparison = (
            comparison_by_scenario[
                scenario
            ]
        )

        score = float(
            assessment["score"]
        )

        error = float(
            comparison[
                "maximum_final_error_m"
            ]
        )

        soc = float(
            comparison[
                "minimum_soc_percent"
            ]
        )

        energy_risk = max(
            0.0,
            30.0 - soc,
        )

        scenarios.append(
            scenario
        )

        resilience_scores.append(
            score
        )

        formation_errors.append(
            error
        )

        bubble_sizes.append(
            120.0
            + energy_risk * 22.0
        )

    figure, axis = plt.subplots(
        figsize=(11.5, 7.0)
    )

    axis.scatter(
        resilience_scores,
        formation_errors,
        s=bubble_sizes,
        alpha=0.65,
        edgecolors="black",
        linewidths=0.8,
    )

    for scenario, score, error in zip(
        scenarios,
        resilience_scores,
        formation_errors,
    ):
        axis.annotate(
            scenario,
            (
                score,
                error,
            ),
            xytext=(
                5,
                5,
            ),
            textcoords="offset points",
            fontsize=8,
        )

    axis.axvline(
        75.0,
        linestyle="--",
        label="Límite degradado: 75",
    )

    axis.axvline(
        50.0,
        linestyle=":",
        label="Límite crítico: 50",
    )

    axis.axhline(
        0.50,
        linestyle="--",
        label="Error degradado: 0.50 m",
    )

    axis.set_title(
        "Mapa de criticidad y resiliencia de los escenarios"
    )

    axis.set_xlabel(
        "Índice de resiliencia [0–100]"
    )

    axis.set_ylabel(
        "Error final máximo de formación [m]"
    )

    axis.set_xlim(
        45.0,
        105.0,
    )

    axis.grid(
        alpha=0.30,
    )

    axis.legend(
        loc="upper left",
    )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem=(
            "04_mapa_criticidad_resiliencia"
        ),
    )


def generate_advanced_visualizations(
    comparison_csv_path: str | Path,
    assessment_csv_path: str | Path,
    output_directory: str | Path,
) -> dict[
    str,
    dict[str, Path],
]:
    """Genera el paquete avanzado de la Fase 16.4."""

    comparison_rows = load_comparison_rows(
        comparison_csv_path
    )

    assessment_rows = load_assessment_rows(
        assessment_csv_path
    )

    return {
        "operational_heatmap": (
            plot_operational_heatmap(
                comparison_rows=(
                    comparison_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "multidomain_radar": (
            plot_multidomain_radar(
                comparison_rows=(
                    comparison_rows
                ),
                assessment_rows=(
                    assessment_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "availability_fedavg": (
            plot_availability_and_federated(
                comparison_rows=(
                    comparison_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
        "criticality_map": (
            plot_resilience_criticality_map(
                comparison_rows=(
                    comparison_rows
                ),
                assessment_rows=(
                    assessment_rows
                ),
                output_directory=(
                    output_directory
                ),
            )
        ),
    }