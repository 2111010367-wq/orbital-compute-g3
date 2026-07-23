"""
Generación de gráficas temporales para los ocho escenarios G3.
"""

from __future__ import annotations

from pathlib import Path

from orbital_compute.temporal_visualization_g3 import (
    generate_all_temporal_charts,
)


RESULTS_DIRECTORY = (
    Path("resultados")
    / "escenarios_fase15"
)

OUTPUT_DIRECTORY = (
    Path("resultados")
    / "graficas_fase16"
    / "series_temporales"
)


def main() -> None:
    """Genera todas las gráficas temporales."""

    print("=" * 92)
    print(
        "FASE 16.2 - GRÁFICAS TEMPORALES "
        "DE LOS ESCENARIOS G3"
    )
    print("=" * 92)

    campaign = (
        generate_all_temporal_charts(
            results_directory=(
                RESULTS_DIRECTORY
            ),
            output_directory=(
                OUTPUT_DIRECTORY
            ),
        )
    )

    total_charts = 0
    total_files = 0

    for (
        scenario_name,
        charts,
    ) in campaign.items():
        chart_count = len(
            charts
        )

        file_count = sum(
            len(files)
            for files in charts.values()
        )

        total_charts += chart_count
        total_files += file_count

        print(
            f"{scenario_name:<24}: "
            f"{chart_count} gráficas, "
            f"{file_count} archivos"
        )

    print("-" * 92)

    print(
        f"Escenarios procesados : "
        f"{len(campaign)}"
    )

    print(
        f"Gráficas generadas    : "
        f"{total_charts}"
    )

    print(
        f"Archivos exportados   : "
        f"{total_files}"
    )

    print(
        "Directorio de salida : "
        f"{OUTPUT_DIRECTORY.resolve()}"
    )

    print("=" * 92)
    print(
        "FASE 16.2 EJECUTADA CORRECTAMENTE"
    )
    print("=" * 92)


if __name__ == "__main__":
    main()