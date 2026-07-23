"""Generación de figuras de FedAvg, supervisor cognitivo y eventos G3."""

from __future__ import annotations

from pathlib import Path

from orbital_compute.intelligence_visualization_g3 import (
    generate_all_intelligence_charts,
)


RESULTS_DIRECTORY = (
    Path("resultados")
    / "escenarios_fase15"
)

OUTPUT_DIRECTORY = (
    Path("resultados")
    / "graficas_fase16"
    / "inteligencia_eventos"
)


def main() -> None:
    """Genera la campaña completa de visualización inteligente."""

    print("=" * 96)
    print(
        "FASE 16.3 - FEDAVG, SUPERVISOR COGNITIVO "
        "Y EVENTOS"
    )
    print("=" * 96)

    campaign = generate_all_intelligence_charts(
        results_directory=RESULTS_DIRECTORY,
        output_directory=OUTPUT_DIRECTORY,
    )

    total_charts = 0
    total_files = 0

    for scenario_name, charts in campaign.items():
        chart_count = len(charts)
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

    print("-" * 96)
    print(f"Escenarios procesados : {len(campaign)}")
    print(f"Gráficas generadas    : {total_charts}")
    print(f"Archivos exportados   : {total_files}")
    print(
        "Directorio de salida : "
        f"{OUTPUT_DIRECTORY.resolve()}"
    )
    print("=" * 96)
    print("FASE 16.3 EJECUTADA CORRECTAMENTE")
    print("=" * 96)


if __name__ == "__main__":
    main()
