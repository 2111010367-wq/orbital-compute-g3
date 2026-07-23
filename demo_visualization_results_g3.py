"""Generación del paquete gráfico inicial de la Fase 16."""

from __future__ import annotations

from pathlib import Path

from orbital_compute.visualization_results_g3 import (
    generate_phase16_summary_charts,
)


COMPARISON_CSV = (
    Path("resultados")
    / "comparacion_fase15"
    / "comparacion_escenarios.csv"
)

ASSESSMENT_CSV = (
    Path("resultados")
    / "evaluacion_resiliencia_fase15"
    / "evaluacion_resiliencia.csv"
)

OUTPUT_DIRECTORY = (
    Path("resultados")
    / "graficas_fase16"
    / "resumen_comparativo"
)


def main() -> None:
    """Genera las figuras comparativas."""

    print("=" * 88)
    print(
        "FASE 16.1 - INFRAESTRUCTURA "
        "Y EXPORTACIÓN GRÁFICA"
    )
    print("=" * 88)

    generated_charts = (
        generate_phase16_summary_charts(
            comparison_csv_path=(
                COMPARISON_CSV
            ),
            assessment_csv_path=(
                ASSESSMENT_CSV
            ),
            output_directory=(
                OUTPUT_DIRECTORY
            ),
        )
    )

    print(
        f"Gráficas generadas: "
        f"{len(generated_charts)}"
    )

    for chart_name, files in (
        generated_charts.items()
    ):
        print(f"\n{chart_name}:")

        for file_format, path in files.items():
            print(
                f"  {file_format.upper():>4}: "
                f"{path.resolve()}"
            )

    print("\n")
    print("=" * 88)
    print(
        "FASE 16.1 EJECUTADA CORRECTAMENTE"
    )
    print("=" * 88)


if __name__ == "__main__":
    main()