"""
Métricas comparativas de resiliencia para los escenarios G3.

Este módulo convierte los resultados del simulador integrado
en indicadores normalizados que pueden compararse contra
el escenario nominal.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ScenarioMetrics:
    """Indicadores principales de un escenario."""

    scenario: str
    snapshot_count: int
    event_count: int

    maximum_final_formation_error_m: float

    minimum_soc: float
    minimum_link_margin_db: float

    link_unavailable_snapshot_count: int
    disabled_satellite_snapshot_count: int

    link_snapshot_availability: float
    node_snapshot_availability: float

    federated_rounds_completed: int
    federated_rounds_cancelled: int
    federated_completion_rate: float

    final_global_accuracy: float

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Convierte las métricas en un diccionario."""

        return asdict(self)


def _require_mapping(
    value: Any,
    section_name: str,
) -> Mapping[str, Any]:
    """Comprueba que una sección sea un diccionario."""

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(
            f"La sección {section_name} "
            "debe ser un diccionario"
        )

    return value


def extract_scenario_metrics(
    result: Mapping[str, Any],
) -> ScenarioMetrics:
    """Extrae las métricas principales de un resultado."""

    if "summary" not in result:
        raise ValueError(
            "El resultado no contiene summary"
        )

    if "snapshots" not in result:
        raise ValueError(
            "El resultado no contiene snapshots"
        )

    summary = _require_mapping(
        result["summary"],
        "summary",
    )

    snapshots = result["snapshots"]

    if not isinstance(
        snapshots,
        list,
    ):
        raise ValueError(
            "snapshots debe ser una lista"
        )

    snapshot_count = len(
        snapshots
    )

    if snapshot_count <= 0:
        raise ValueError(
            "El resultado debe contener snapshots"
        )

    scenario = str(
        summary["scenario"]
    )

    final_errors = _require_mapping(
        summary[
            "final_formation_errors_m"
        ],
        "final_formation_errors_m",
    )

    if not final_errors:
        raise ValueError(
            "No existen errores finales "
            "de formación"
        )

    maximum_final_error = max(
        float(value)
        for value
        in final_errors.values()
    )

    unavailable_count = int(
        summary[
            "link_unavailable_snapshot_count"
        ]
    )

    disabled_count = int(
        summary[
            "disabled_satellite_snapshot_count"
        ]
    )

    if not 0 <= unavailable_count <= snapshot_count:
        raise ValueError(
            "El conteo de enlaces no disponibles "
            "es inválido"
        )

    if not 0 <= disabled_count <= snapshot_count:
        raise ValueError(
            "El conteo de nodos deshabilitados "
            "es inválido"
        )

    completed_rounds = int(
        summary[
            "federated_rounds_completed"
        ]
    )

    cancelled_rounds = int(
        summary[
            "federated_rounds_cancelled"
        ]
    )

    total_federated_attempts = (
        completed_rounds
        + cancelled_rounds
    )

    if total_federated_attempts > 0:
        federated_completion_rate = (
            completed_rounds
            / total_federated_attempts
        )
    else:
        federated_completion_rate = 0.0

    return ScenarioMetrics(
        scenario=scenario,
        snapshot_count=snapshot_count,
        event_count=int(
            summary["event_count"]
        ),
        maximum_final_formation_error_m=(
            maximum_final_error
        ),
        minimum_soc=float(
            summary["minimum_soc"]
        ),
        minimum_link_margin_db=float(
            summary[
                "minimum_link_margin_db"
            ]
        ),
        link_unavailable_snapshot_count=(
            unavailable_count
        ),
        disabled_satellite_snapshot_count=(
            disabled_count
        ),
        link_snapshot_availability=(
            1.0
            - unavailable_count
            / snapshot_count
        ),
        node_snapshot_availability=(
            1.0
            - disabled_count
            / snapshot_count
        ),
        federated_rounds_completed=(
            completed_rounds
        ),
        federated_rounds_cancelled=(
            cancelled_rounds
        ),
        federated_completion_rate=(
            federated_completion_rate
        ),
        final_global_accuracy=float(
            summary[
                "final_global_accuracy"
            ]
        ),
    )


def compare_against_nominal(
    metrics: ScenarioMetrics,
    nominal: ScenarioMetrics,
) -> dict[str, float | str]:
    """Compara un escenario con la referencia nominal."""

    return {
        "scenario": metrics.scenario,
        "delta_maximum_final_formation_error_m": (
            metrics
            .maximum_final_formation_error_m
            - nominal
            .maximum_final_formation_error_m
        ),
        "delta_minimum_soc_percentage_points": (
            (
                metrics.minimum_soc
                - nominal.minimum_soc
            )
            * 100.0
        ),
        "delta_minimum_link_margin_db": (
            metrics.minimum_link_margin_db
            - nominal.minimum_link_margin_db
        ),
        "delta_link_availability_percentage_points": (
            (
                metrics.link_snapshot_availability
                - nominal.link_snapshot_availability
            )
            * 100.0
        ),
        "delta_node_availability_percentage_points": (
            (
                metrics.node_snapshot_availability
                - nominal.node_snapshot_availability
            )
            * 100.0
        ),
        "delta_federated_completion_percentage_points": (
            (
                metrics.federated_completion_rate
                - nominal.federated_completion_rate
            )
            * 100.0
        ),
        "delta_final_accuracy_percentage_points": (
            (
                metrics.final_global_accuracy
                - nominal.final_global_accuracy
            )
            * 100.0
        ),
    }


def load_scenario_result(
    path: str | Path,
) -> dict[str, Any]:
    """Carga un resultado JSON de escenario."""

    json_path = Path(
        path
    )

    if not json_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {json_path}"
        )

    result = json.loads(
        json_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "El contenido del JSON "
            "debe ser un diccionario"
        )

    return result


def metrics_from_file(
    path: str | Path,
) -> ScenarioMetrics:
    """Carga un JSON y obtiene sus métricas."""

    return extract_scenario_metrics(
        load_scenario_result(
            path
        )
    )