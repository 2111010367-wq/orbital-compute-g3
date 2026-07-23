"""
Comparación de los escenarios nominales y de falla G3.

Este programa carga los ocho resultados de la Fase 15,
extrae sus métricas de resiliencia y compara cada escenario
contra la operación nominal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orbital_compute.resilience_metrics_g3 import (
    ScenarioMetrics,
    compare_against_nominal,
    metrics_from_file,
)
from orbital_compute.scenarios_g3 import (
    ScenarioName,
)


DEFAULT_RESULTS_DIRECTORY = (
    Path("resultados")
    / "escenarios_fase15"
)


def scenario_result_path(
    results_directory: str | Path,
    scenario: ScenarioName,
) -> Path:
    """Construye la ruta del JSON de un escenario."""

    return (
        Path(results_directory)
        / f"{scenario.value.lower()}.json"
    )


def load_all_scenario_metrics(
    results_directory: str | Path,
) -> dict[ScenarioName, ScenarioMetrics]:
    """Carga las métricas de los ocho escenarios."""

    metrics_by_scenario: dict[
        ScenarioName,
        ScenarioMetrics,
    ] = {}

    for scenario in ScenarioName:
        result_path = scenario_result_path(
            results_directory=results_directory,
            scenario=scenario,
        )

        if not result_path.exists():
            raise FileNotFoundError(
                "No se encontró el resultado del escenario "
                f"{scenario.value}: {result_path}"
            )

        metrics = metrics_from_file(
            result_path
        )

        if metrics.scenario != scenario.value:
            raise ValueError(
                "El escenario registrado en el JSON "
                f"no coincide con {scenario.value}"
            )

        metrics_by_scenario[
            scenario
        ] = metrics

    return metrics_by_scenario


def build_comparison_rows(
    results_directory: str | Path = (
        DEFAULT_RESULTS_DIRECTORY
    ),
) -> list[dict[str, Any]]:
    """Construye las filas de comparación."""

    metrics_by_scenario = (
        load_all_scenario_metrics(
            results_directory
        )
    )

    nominal_metrics = metrics_by_scenario[
        ScenarioName.NOMINAL
    ]

    rows: list[dict[str, Any]] = []

    for scenario in ScenarioName:
        metrics = metrics_by_scenario[
            scenario
        ]

        differences = compare_against_nominal(
            metrics=metrics,
            nominal=nominal_metrics,
        )

        rows.append(
            {
                "scenario": scenario.value,
                "maximum_final_error_m": (
                    metrics
                    .maximum_final_formation_error_m
                ),
                "delta_error_m": (
                    differences[
                        "delta_maximum_final_formation_error_m"
                    ]
                ),
                "minimum_soc_percent": (
                    metrics.minimum_soc
                    * 100.0
                ),
                "delta_soc_pp": (
                    differences[
                        "delta_minimum_soc_percentage_points"
                    ]
                ),
                "minimum_margin_db": (
                    metrics.minimum_link_margin_db
                ),
                "delta_margin_db": (
                    differences[
                        "delta_minimum_link_margin_db"
                    ]
                ),
                "link_availability_percent": (
                    metrics
                    .link_snapshot_availability
                    * 100.0
                ),
                "delta_link_availability_pp": (
                    differences[
                        "delta_link_availability_percentage_points"
                    ]
                ),
                "node_availability_percent": (
                    metrics
                    .node_snapshot_availability
                    * 100.0
                ),
                "delta_node_availability_pp": (
                    differences[
                        "delta_node_availability_percentage_points"
                    ]
                ),
                "federated_completion_percent": (
                    metrics
                    .federated_completion_rate
                    * 100.0
                ),
                "delta_federated_completion_pp": (
                    differences[
                        "delta_federated_completion_percentage_points"
                    ]
                ),
                "final_accuracy_percent": (
                    metrics.final_global_accuracy
                    * 100.0
                ),
                "delta_accuracy_pp": (
                    differences[
                        "delta_final_accuracy_percentage_points"
                    ]
                ),
            }
        )

    return rows


def print_separator() -> None:
    """Imprime una línea separadora."""

    print("=" * 146)


def print_comparison_table(
    rows: list[dict[str, Any]],
) -> None:
    """Muestra la tabla comparativa en consola."""

    print_separator()

    print(
        "FASE 15.3.2 - COMPARACIÓN DE "
        "ESCENARIOS CONTRA OPERACIÓN NOMINAL"
    )

    print_separator()

    header = (
        f"{'ESCENARIO':<23}"
        f"{'ERR(m)':>9}"
        f"{'dERR':>9}"
        f"{'SOC(%)':>9}"
        f"{'dSOC':>9}"
        f"{'MARGEN':>10}"
        f"{'dMARGEN':>10}"
        f"{'ISL(%)':>9}"
        f"{'NODO(%)':>10}"
        f"{'FED(%)':>9}"
        f"{'ACC(%)':>9}"
    )

    print(header)
    print("-" * 146)

    for row in rows:
        print(
            f"{row['scenario']:<23}"
            f"{row['maximum_final_error_m']:>9.3f}"
            f"{row['delta_error_m']:>9.3f}"
            f"{row['minimum_soc_percent']:>9.2f}"
            f"{row['delta_soc_pp']:>9.2f}"
            f"{row['minimum_margin_db']:>10.2f}"
            f"{row['delta_margin_db']:>10.2f}"
            f"{row['link_availability_percent']:>9.2f}"
            f"{row['node_availability_percent']:>10.2f}"
            f"{row['federated_completion_percent']:>9.2f}"
            f"{row['final_accuracy_percent']:>9.2f}"
        )

    print_separator()

    print("Leyenda:")
    print("  ERR(m)   : error final máximo de formación.")
    print("  dERR     : variación respecto al escenario nominal.")
    print("  SOC(%)   : estado de carga mínimo.")
    print("  dSOC     : diferencia de SOC en puntos porcentuales.")
    print("  MARGEN   : margen mínimo del enlace Ka en dB.")
    print("  dMARGEN  : variación del margen respecto al nominal.")
    print("  ISL(%)   : disponibilidad temporal de enlaces.")
    print("  NODO(%)  : disponibilidad temporal de satélites.")
    print("  FED(%)   : porcentaje de rondas FedAvg completadas.")
    print("  ACC(%)   : exactitud global final.")

    print_separator()


def print_engineering_analysis(
    rows: list[dict[str, Any]],
) -> None:
    """Presenta las degradaciones principales."""

    non_nominal_rows = [
        row
        for row in rows
        if row["scenario"]
        != ScenarioName.NOMINAL.value
    ]

    worst_formation = max(
        non_nominal_rows,
        key=lambda row: (
            row["maximum_final_error_m"]
        ),
    )

    lowest_soc = min(
        non_nominal_rows,
        key=lambda row: (
            row["minimum_soc_percent"]
        ),
    )

    lowest_margin = min(
        non_nominal_rows,
        key=lambda row: (
            row["minimum_margin_db"]
        ),
    )

    lowest_link_availability = min(
        non_nominal_rows,
        key=lambda row: (
            row[
                "link_availability_percent"
            ]
        ),
    )

    lowest_node_availability = min(
        non_nominal_rows,
        key=lambda row: (
            row[
                "node_availability_percent"
            ]
        ),
    )

    lowest_federated_completion = min(
        non_nominal_rows,
        key=lambda row: (
            row[
                "federated_completion_percent"
            ]
        ),
    )

    print("\nANÁLISIS AUTOMÁTICO DE INGENIERÍA")
    print("-" * 80)

    print(
        "Mayor error final de formación : "
        f"{worst_formation['scenario']} "
        f"({worst_formation['maximum_final_error_m']:.3f} m)"
    )

    print(
        "Menor SOC registrado           : "
        f"{lowest_soc['scenario']} "
        f"({lowest_soc['minimum_soc_percent']:.2f} %)"
    )

    print(
        "Menor margen del enlace Ka     : "
        f"{lowest_margin['scenario']} "
        f"({lowest_margin['minimum_margin_db']:.2f} dB)"
    )

    print(
        "Menor disponibilidad ISL       : "
        f"{lowest_link_availability['scenario']} "
        f"({lowest_link_availability['link_availability_percent']:.2f} %)"
    )

    print(
        "Menor disponibilidad de nodos  : "
        f"{lowest_node_availability['scenario']} "
        f"({lowest_node_availability['node_availability_percent']:.2f} %)"
    )

    print(
        "Menor tasa FedAvg completada    : "
        f"{lowest_federated_completion['scenario']} "
        f"({lowest_federated_completion['federated_completion_percent']:.2f} %)"
    )


def main() -> None:
    """Ejecuta la comparación completa."""

    rows = build_comparison_rows(
        DEFAULT_RESULTS_DIRECTORY
    )

    print_comparison_table(
        rows
    )

    print_engineering_analysis(
        rows
    )

    print(
        "\nFASE 15.3.2 EJECUTADA "
        "CORRECTAMENTE"
    )


if __name__ == "__main__":
    main()