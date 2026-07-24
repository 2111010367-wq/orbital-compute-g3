"""Comprobación del cargador de datos del dashboard G3."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_g3.data_loader import (
    SCENARIO_ORDER,
    build_dashboard_dataset,
)


SCENARIOS_DIRECTORY = (
    Path("resultados")
    / "escenarios_fase15"
)

COMPARISON_JSON = (
    Path("resultados")
    / "comparacion_fase15"
    / "comparacion_escenarios.json"
)

ASSESSMENT_JSON = (
    Path("resultados")
    / "evaluacion_resiliencia_fase15"
    / "evaluacion_resiliencia.json"
)


def assessment_score(
    row: dict,
) -> object:
    """Obtiene el puntaje disponible."""

    return row.get(
        "score",
        row.get(
            "resilience_score",
            "N/D",
        ),
    )


def main() -> None:
    """Carga y resume los datos reales."""

    print("=" * 96)
    print(
        "FASE 17.1.2 - CARGADOR DE DATOS "
        "DEL DASHBOARD G3"
    )
    print("=" * 96)

    dataset = build_dashboard_dataset(
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

    print(
        f"Escenarios cargados : "
        f"{dataset['scenario_count']}"
    )

    print("-" * 96)

    for scenario in SCENARIO_ORDER:
        summary = (
            dataset[
                "scenario_summaries"
            ][scenario]
        )

        assessment = (
            dataset[
                "assessment"
            ][scenario]
        )

        score = assessment_score(
            assessment
        )

        print(
            f"{scenario:<24} | "
            f"snapshots={summary['snapshot_count']:>3} | "
            f"eventos={summary['event_count']:>3} | "
            f"satélites={summary['satellite_count']} | "
            f"duración={summary['duration_min']:.1f} min | "
            f"resiliencia={score}"
        )

    json.dumps(
        dataset,
        ensure_ascii=False,
    )

    print("-" * 96)
    print(
        "CONJUNTO COMPLETO Y SERIALIZABLE EN JSON"
    )
    print("=" * 96)
    print(
        "FASE 17.1.2 EJECUTADA CORRECTAMENTE"
    )
    print("=" * 96)


if __name__ == "__main__":
    main()