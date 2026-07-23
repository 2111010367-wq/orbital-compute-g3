"""
Ejecución y validación de escenarios nominales y de falla G3.

Esta demostración ejecuta los ocho escenarios definidos en
scenarios_g3.py y exporta un archivo JSON independiente
para cada escenario.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orbital_compute.integrated_simulator_g3 import (
    IntegratedG3Simulator,
    save_integrated_result,
)
from orbital_compute.scenarios_g3 import (
    ScenarioName,
)


DEFAULT_OUTPUT_DIRECTORY = (
    Path("resultados")
    / "escenarios_fase15"
)


def print_separator() -> None:
    """Imprime una línea separadora."""

    print("=" * 94)


def validate_result(
    result: dict[str, Any],
    expected_scenario: ScenarioName,
) -> None:
    """Valida la estructura básica de un resultado."""

    required_sections = {
        "scenario",
        "snapshots",
        "events",
        "federated_rounds",
        "summary",
    }

    missing_sections = (
        required_sections
        - set(result)
    )

    if missing_sections:
        raise RuntimeError(
            "Resultado incompleto. "
            "Faltan las secciones: "
            f"{sorted(missing_sections)}"
        )

    summary = result["summary"]

    if (
        summary["scenario"]
        != expected_scenario.value
    ):
        raise RuntimeError(
            "El escenario del resultado "
            "no coincide con el solicitado"
        )

    if summary["satellite_count"] != 3:
        raise RuntimeError(
            "La simulación debe contener "
            "exactamente tres satélites"
        )

    if len(result["snapshots"]) == 0:
        raise RuntimeError(
            "La simulación no generó snapshots"
        )


def run_single_scenario(
    scenario: ScenarioName,
    output_directory: str | Path,
    duration_s: float = 3600.0,
    time_step_s: float = 60.0,
    federated_interval_s: float = 600.0,
    random_seed: int = 42,
) -> tuple[dict[str, Any], Path]:
    """Ejecuta y exporta un escenario."""

    simulator = IntegratedG3Simulator(
        duration_s=duration_s,
        time_step_s=time_step_s,
        federated_interval_s=(
            federated_interval_s
        ),
        random_seed=random_seed,
        scenario=scenario,
    )

    result = simulator.run()

    validate_result(
        result=result,
        expected_scenario=scenario,
    )

    output_path = (
        Path(output_directory)
        / f"{scenario.value.lower()}.json"
    )

    saved_path = save_integrated_result(
        result=result,
        output_path=output_path,
    )

    return result, saved_path


def run_all_scenarios(
    output_directory: str | Path = (
        DEFAULT_OUTPUT_DIRECTORY
    ),
    verbose: bool = True,
) -> dict[str, Path]:
    """Ejecuta todos los escenarios disponibles."""

    generated_files: dict[str, Path] = {}

    if verbose:
        print_separator()
        print(
            "FASE 15.2.3 - VALIDACIÓN "
            "DE ESCENARIOS G3"
        )
        print_separator()

    for index, scenario in enumerate(
        ScenarioName,
        start=1,
    ):
        if verbose:
            print(
                f"\n[{index}/{len(ScenarioName)}] "
                f"Ejecutando {scenario.value}..."
            )

        result, saved_path = (
            run_single_scenario(
                scenario=scenario,
                output_directory=(
                    output_directory
                ),
            )
        )

        generated_files[
            scenario.value
        ] = saved_path

        summary = result["summary"]

        if verbose:
            final_errors = summary[
                "final_formation_errors_m"
            ]

            maximum_final_error = max(
                final_errors.values()
            )

            print(
                f"  Snapshots                : "
                f"{len(result['snapshots'])}"
            )

            print(
                f"  Eventos                   : "
                f"{summary['event_count']}"
            )

            print(
                f"  Error final máximo        : "
                f"{maximum_final_error:.3f} m"
            )

            print(
                f"  SOC mínimo                : "
                f"{summary['minimum_soc'] * 100:.2f} %"
            )

            print(
                f"  Margen mínimo Ka          : "
                f"{summary['minimum_link_margin_db']:.2f} dB"
            )

            print(
                f"  Enlaces no disponibles    : "
                f"{summary['link_unavailable_snapshot_count']}"
            )

            print(
                f"  Satélites deshabilitados  : "
                f"{summary['disabled_satellite_snapshot_count']}"
            )

            print(
                "  FedAvg completadas/"
                "canceladas: "
                f"{summary['federated_rounds_completed']}/"
                f"{summary['federated_rounds_cancelled']}"
            )

            print(
                f"  Exactitud final           : "
                f"{summary['final_global_accuracy'] * 100:.2f} %"
            )

            print(
                f"  JSON                      : "
                f"{saved_path.resolve()}"
            )

    if verbose:
        print("\n")
        print_separator()
        print(
            "LOS OCHO ESCENARIOS FUERON "
            "EJECUTADOS CORRECTAMENTE"
        )
        print_separator()

        print(
            f"Directorio de resultados: "
            f"{Path(output_directory).resolve()}"
        )

    return generated_files


def main() -> None:
    """Ejecuta la demostración completa."""

    run_all_scenarios()


if __name__ == "__main__":
    main()