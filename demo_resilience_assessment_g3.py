"""
Clasificación profesional de resiliencia de la Fase 15.
"""

from __future__ import annotations

from pathlib import Path

from demo_compare_scenarios_g3 import (
    DEFAULT_RESULTS_DIRECTORY,
    build_comparison_rows,
)
from orbital_compute.resilience_assessment_g3 import (
    assess_campaign,
    export_assessment_bundle,
    rank_assessments,
    select_critical_scenario,
)


DEFAULT_OUTPUT_DIRECTORY = (
    Path("resultados")
    / "evaluacion_resiliencia_fase15"
)


def print_separator() -> None:
    """Imprime una línea separadora."""

    print("=" * 92)


def main() -> None:
    """Ejecuta la evaluación de resiliencia."""

    print_separator()
    print(
        "FASE 15.3.4 - CLASIFICACIÓN "
        "PROFESIONAL DE RESILIENCIA"
    )
    print_separator()

    rows = build_comparison_rows(
        DEFAULT_RESULTS_DIRECTORY
    )

    assessments = assess_campaign(
        rows
    )

    ranking = rank_assessments(
        assessments
    )

    print(
        f"{'POS':>4} "
        f"{'ESCENARIO':<24}"
        f"{'PUNTAJE':>10} "
        f"{'CLASIFICACIÓN':>16}"
    )

    print("-" * 92)

    for position, assessment in enumerate(
        ranking,
        start=1,
    ):
        print(
            f"{position:>4} "
            f"{assessment.scenario:<24}"
            f"{assessment.score:>10.2f} "
            f"{assessment.level.value:>16}"
        )

        for finding in assessment.findings:
            print(
                f"     - {finding}"
            )

    critical = select_critical_scenario(
        assessments
    )

    generated_files = (
        export_assessment_bundle(
            assessments=assessments,
            output_directory=(
                DEFAULT_OUTPUT_DIRECTORY
            ),
        )
    )

    print("\n")
    print_separator()
    print("RESULTADO PRINCIPAL")
    print_separator()

    print(
        "Escenario más crítico : "
        f"{critical.scenario}"
    )

    print(
        "Puntaje de resiliencia: "
        f"{critical.score:.2f}/100"
    )

    print(
        "Clasificación         : "
        f"{critical.level.value}"
    )

    print(
        "\nArchivo CSV : "
        f"{generated_files['csv'].resolve()}"
    )

    print(
        "Archivo JSON: "
        f"{generated_files['json'].resolve()}"
    )

    print_separator()
    print(
        "FASE 15.3.4 EJECUTADA "
        "CORRECTAMENTE"
    )
    print_separator()


if __name__ == "__main__":
    main()