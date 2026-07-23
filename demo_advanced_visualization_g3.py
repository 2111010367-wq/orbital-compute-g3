"""Ejecución de la comparación visual avanzada G3."""

from __future__ import annotations

from pathlib import Path

from orbital_compute.advanced_visualization_g3 import (
    generate_advanced_visualizations,
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
    / "comparacion_avanzada"
)


def main() -> None:
    """Genera las figuras avanzadas."""

    print("=" * 92)
    print(
        "FASE 16.4 - COMPARACIÓN "
        "VISUAL AVANZADA G3"
    )
    print("=" * 92)

    charts = generate_advanced_visualizations(
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

    total_files = sum(
        len(files)
        for files in charts.values()
    )

    print(
        f"Gráficas generadas  : "
        f"{len(charts)}"
    )

    print(
        f"Archivos exportados : "
        f"{total_files}"
    )

    print(
        "Directorio de salida: "
        f"{OUTPUT_DIRECTORY.resolve()}"
    )

    print("=" * 92)
    print(
        "FASE 16.4 EJECUTADA CORRECTAMENTE"
    )
    print("=" * 92)


if __name__ == "__main__":
    main()