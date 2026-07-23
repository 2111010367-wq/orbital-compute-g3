"""
Evaluación profesional de resiliencia de los escenarios G3.

El módulo asigna:

- Penalizaciones normalizadas.
- Puntaje de resiliencia entre 0 y 100.
- Clasificación operativa.
- Hallazgos técnicos.
- Identificación automática del escenario crítico.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class ResilienceLevel(str, Enum):
    """Niveles de resiliencia del sistema."""

    ROBUST = "ROBUSTO"
    ACCEPTABLE = "ACEPTABLE"
    DEGRADED = "DEGRADADO"
    CRITICAL = "CRITICO"


RESILIENCE_WEIGHTS = {
    "formation": 0.20,
    "energy": 0.20,
    "rf_margin": 0.20,
    "link_availability": 0.15,
    "node_availability": 0.10,
    "federated_learning": 0.10,
    "global_accuracy": 0.05,
}


@dataclass(frozen=True)
class ResilienceAssessment:
    """Resultado de evaluación de un escenario."""

    scenario: str
    score: float
    level: ResilienceLevel

    formation_penalty: float
    energy_penalty: float
    rf_margin_penalty: float
    link_availability_penalty: float
    node_availability_penalty: float
    federated_learning_penalty: float
    global_accuracy_penalty: float

    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convierte la evaluación en un diccionario."""

        return {
            "scenario": self.scenario,
            "score": self.score,
            "level": self.level.value,
            "formation_penalty": (
                self.formation_penalty
            ),
            "energy_penalty": (
                self.energy_penalty
            ),
            "rf_margin_penalty": (
                self.rf_margin_penalty
            ),
            "link_availability_penalty": (
                self.link_availability_penalty
            ),
            "node_availability_penalty": (
                self.node_availability_penalty
            ),
            "federated_learning_penalty": (
                self.federated_learning_penalty
            ),
            "global_accuracy_penalty": (
                self.global_accuracy_penalty
            ),
            "findings": list(self.findings),
        }


def _clamp(value: float) -> float:
    """Limita un valor al intervalo [0, 1]."""

    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )


def _relative_degradation(
    current_value: float,
    reference_value: float,
) -> float:
    """Calcula una degradación relativa normalizada."""

    if reference_value <= 0.0:
        return 0.0

    return _clamp(
        (
            reference_value
            - current_value
        )
        / reference_value
    )


def _validate_row(
    row: Mapping[str, Any],
) -> None:
    """Valida los campos necesarios."""

    required_fields = {
        "scenario",
        "maximum_final_error_m",
        "minimum_soc_percent",
        "minimum_margin_db",
        "link_availability_percent",
        "node_availability_percent",
        "federated_completion_percent",
        "final_accuracy_percent",
    }

    missing_fields = (
        required_fields
        - set(row)
    )

    if missing_fields:
        raise ValueError(
            "Fila comparativa incompleta. "
            f"Faltan: {sorted(missing_fields)}"
        )


def calculate_penalties(
    row: Mapping[str, Any],
    nominal_row: Mapping[str, Any],
) -> dict[str, float]:
    """Calcula las penalizaciones normalizadas."""

    _validate_row(row)
    _validate_row(nominal_row)

    formation_degradation_m = max(
        0.0,
        float(
            row[
                "maximum_final_error_m"
            ]
        )
        - float(
            nominal_row[
                "maximum_final_error_m"
            ]
        ),
    )

    return {
        "formation": _clamp(
            formation_degradation_m
            / 1.0
        ),
        "energy": _relative_degradation(
            current_value=float(
                row[
                    "minimum_soc_percent"
                ]
            ),
            reference_value=float(
                nominal_row[
                    "minimum_soc_percent"
                ]
            ),
        ),
        "rf_margin": _relative_degradation(
            current_value=float(
                row[
                    "minimum_margin_db"
                ]
            ),
            reference_value=float(
                nominal_row[
                    "minimum_margin_db"
                ]
            ),
        ),
        "link_availability": (
            _relative_degradation(
                current_value=float(
                    row[
                        "link_availability_percent"
                    ]
                ),
                reference_value=float(
                    nominal_row[
                        "link_availability_percent"
                    ]
                ),
            )
        ),
        "node_availability": (
            _relative_degradation(
                current_value=float(
                    row[
                        "node_availability_percent"
                    ]
                ),
                reference_value=float(
                    nominal_row[
                        "node_availability_percent"
                    ]
                ),
            )
        ),
        "federated_learning": (
            _relative_degradation(
                current_value=float(
                    row[
                        "federated_completion_percent"
                    ]
                ),
                reference_value=float(
                    nominal_row[
                        "federated_completion_percent"
                    ]
                ),
            )
        ),
        "global_accuracy": (
            _relative_degradation(
                current_value=float(
                    row[
                        "final_accuracy_percent"
                    ]
                ),
                reference_value=float(
                    nominal_row[
                        "final_accuracy_percent"
                    ]
                ),
            )
        ),
    }


def build_findings(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    """Detecta condiciones degradadas y críticas."""

    _validate_row(row)

    findings: list[str] = []

    formation_error = float(
        row["maximum_final_error_m"]
    )

    minimum_soc = float(
        row["minimum_soc_percent"]
    )

    minimum_margin = float(
        row["minimum_margin_db"]
    )

    link_availability = float(
        row["link_availability_percent"]
    )

    node_availability = float(
        row["node_availability_percent"]
    )

    federated_completion = float(
        row["federated_completion_percent"]
    )

    final_accuracy = float(
        row["final_accuracy_percent"]
    )

    if formation_error >= 1.0:
        findings.append(
            "CRITICO: error de formación "
            "igual o superior a 1 m."
        )

    elif formation_error >= 0.50:
        findings.append(
            "DEGRADADO: error de formación "
            "igual o superior a 0.50 m."
        )

    if minimum_soc < 15.0:
        findings.append(
            "CRITICO: SOC inferior al 15 %."
        )

    elif minimum_soc < 20.0:
        findings.append(
            "DEGRADADO: SOC inferior al 20 %."
        )

    if minimum_margin < 3.0:
        findings.append(
            "CRITICO: margen Ka inferior a 3 dB."
        )

    elif minimum_margin < 10.0:
        findings.append(
            "DEGRADADO: margen Ka inferior a 10 dB."
        )

    if link_availability < 80.0:
        findings.append(
            "CRITICO: disponibilidad ISL "
            "inferior al 80 %."
        )

    elif link_availability < 95.0:
        findings.append(
            "DEGRADADO: disponibilidad ISL "
            "inferior al 95 %."
        )

    if node_availability < 90.0:
        findings.append(
            "CRITICO: disponibilidad de nodos "
            "inferior al 90 %."
        )

    elif node_availability < 98.0:
        findings.append(
            "DEGRADADO: disponibilidad de nodos "
            "inferior al 98 %."
        )

    if federated_completion < 40.0:
        findings.append(
            "CRITICO: menos del 40 % de rondas "
            "FedAvg fueron completadas."
        )

    elif federated_completion < 60.0:
        findings.append(
            "DEGRADADO: menos del 60 % de rondas "
            "FedAvg fueron completadas."
        )

    if final_accuracy < 80.0:
        findings.append(
            "CRITICO: exactitud global "
            "inferior al 80 %."
        )

    elif final_accuracy < 90.0:
        findings.append(
            "DEGRADADO: exactitud global "
            "inferior al 90 %."
        )

    return tuple(findings)


def determine_level(
    score: float,
    findings: Sequence[str],
) -> ResilienceLevel:
    """Determina el nivel final de resiliencia."""

    has_critical_finding = any(
        finding.startswith(
            "CRITICO:"
        )
        for finding in findings
    )

    has_degraded_finding = any(
        finding.startswith(
            "DEGRADADO:"
        )
        for finding in findings
    )

    if has_critical_finding:
        return ResilienceLevel.CRITICAL

    if score < 50.0:
        return ResilienceLevel.CRITICAL

    if has_degraded_finding:
        return ResilienceLevel.DEGRADED

    if score < 75.0:
        return ResilienceLevel.DEGRADED

    if score < 90.0:
        return ResilienceLevel.ACCEPTABLE

    return ResilienceLevel.ROBUST


def assess_scenario(
    row: Mapping[str, Any],
    nominal_row: Mapping[str, Any],
) -> ResilienceAssessment:
    """Evalúa la resiliencia de un escenario."""

    penalties = calculate_penalties(
        row=row,
        nominal_row=nominal_row,
    )

    weighted_penalty = sum(
        RESILIENCE_WEIGHTS[name]
        * penalties[name]
        for name in RESILIENCE_WEIGHTS
    )

    score = max(
        0.0,
        min(
            100.0,
            100.0
            * (
                1.0
                - weighted_penalty
            ),
        ),
    )

    findings = build_findings(
        row
    )

    level = determine_level(
        score=score,
        findings=findings,
    )

    return ResilienceAssessment(
        scenario=str(
            row["scenario"]
        ),
        score=score,
        level=level,
        formation_penalty=(
            penalties["formation"]
        ),
        energy_penalty=(
            penalties["energy"]
        ),
        rf_margin_penalty=(
            penalties["rf_margin"]
        ),
        link_availability_penalty=(
            penalties[
                "link_availability"
            ]
        ),
        node_availability_penalty=(
            penalties[
                "node_availability"
            ]
        ),
        federated_learning_penalty=(
            penalties[
                "federated_learning"
            ]
        ),
        global_accuracy_penalty=(
            penalties[
                "global_accuracy"
            ]
        ),
        findings=findings,
    )


def assess_campaign(
    rows: Sequence[Mapping[str, Any]],
) -> list[ResilienceAssessment]:
    """Evalúa todos los escenarios de una campaña."""

    nominal_row = next(
        (
            row
            for row in rows
            if row["scenario"] == "NOMINAL"
        ),
        None,
    )

    if nominal_row is None:
        raise ValueError(
            "La campaña no contiene "
            "el escenario NOMINAL"
        )

    return [
        assess_scenario(
            row=row,
            nominal_row=nominal_row,
        )
        for row in rows
    ]


def rank_assessments(
    assessments: Sequence[
        ResilienceAssessment
    ],
) -> list[ResilienceAssessment]:
    """Ordena desde el escenario más crítico."""

    return sorted(
        assessments,
        key=lambda assessment: (
            assessment.score,
            assessment.scenario,
        ),
    )


def select_critical_scenario(
    assessments: Sequence[
        ResilienceAssessment
    ],
) -> ResilienceAssessment:
    """Selecciona el escenario de menor resiliencia."""

    failure_assessments = [
        assessment
        for assessment in assessments
        if assessment.scenario != "NOMINAL"
    ]

    if not failure_assessments:
        raise ValueError(
            "No existen escenarios de falla"
        )

    return rank_assessments(
        failure_assessments
    )[0]


def export_assessment_bundle(
    assessments: Sequence[
        ResilienceAssessment
    ],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Exporta la evaluación en CSV y JSON."""

    if not assessments:
        raise ValueError(
            "No existen evaluaciones "
            "para exportar"
        )

    directory = Path(
        output_directory
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    critical = select_critical_scenario(
        assessments
    )

    csv_path = (
        directory
        / "evaluacion_resiliencia.csv"
    )

    json_path = (
        directory
        / "evaluacion_resiliencia.json"
    )

    fieldnames = (
        "scenario",
        "score",
        "level",
        "formation_penalty",
        "energy_penalty",
        "rf_margin_penalty",
        "link_availability_penalty",
        "node_availability_penalty",
        "federated_learning_penalty",
        "global_accuracy_penalty",
        "findings",
    )

    with csv_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for assessment in assessments:
            row = assessment.to_dict()

            row["findings"] = "; ".join(
                assessment.findings
            )

            writer.writerow(row)

    payload = {
        "schema_version": "1.0",
        "critical_scenario": (
            critical.scenario
        ),
        "critical_score": (
            critical.score
        ),
        "scenario_count": len(
            assessments
        ),
        "ranking": [
            assessment.to_dict()
            for assessment
            in rank_assessments(
                assessments
            )
        ],
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return {
        "csv": csv_path,
        "json": json_path,
    }