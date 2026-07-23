"""
Visualización de inteligencia federada, decisiones cognitivas y eventos G3.

El módulo es tolerante a pequeñas variaciones en los nombres de campos de los
JSON generados por el simulador integrado. Produce cuatro figuras por escenario:

1. Evolución de pérdida y exactitud FedAvg.
2. Participación y estado de rondas FedAvg.
3. Distribución de decisiones del supervisor cognitivo.
4. Línea temporal de eventos del sistema.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from orbital_compute.scenarios_g3 import ScenarioName
from orbital_compute.visualization_results_g3 import save_figure_bundle


ROUND_INDEX_KEYS = (
    "round_index",
    "round_number",
    "round",
    "federated_round",
    "index",
)

LOSS_KEYS = (
    "global_loss",
    "loss",
    "model_loss",
    "federated_loss",
)

ACCURACY_KEYS = (
    "global_accuracy",
    "accuracy",
    "model_accuracy",
    "federated_accuracy",
)

PARTICIPANT_KEYS = (
    "participants",
    "participant_ids",
    "clients",
    "selected_clients",
    "eligible_clients",
    "participant_count",
)

EXCLUDED_KEYS = (
    "excluded",
    "excluded_clients",
    "excluded_satellites",
    "rejected_clients",
    "excluded_count",
)

ACTION_KEYS = (
    "cognitive_action",
    "supervisor_action",
    "action",
    "selected_action",
    "decision",
)


def _first_present(
    mapping: Mapping[str, Any],
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    """Devuelve el primer campo existente y no nulo."""

    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]

    return default


def _time_min(record: Mapping[str, Any], fallback: float = 0.0) -> float:
    """Obtiene el tiempo de un registro en minutos."""

    if "time_min" in record:
        return float(record["time_min"])

    if "time_s" in record:
        return float(record["time_s"]) / 60.0

    return float(fallback)


def _count_items(value: Any) -> int:
    """Convierte una lista, conjunto o contador explícito en cantidad."""

    if value is None:
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return max(0, int(value))

    if isinstance(value, Mapping):
        return len(value)

    if isinstance(value, (list, tuple, set)):
        return len(value)

    return 1


def load_scenario_result(path: str | Path) -> dict[str, Any]:
    """Carga y valida un resultado JSON de escenario."""

    result_path = Path(path)

    if not result_path.exists():
        raise FileNotFoundError(
            f"No existe el resultado del escenario: {result_path}"
        )

    result = json.loads(
        result_path.read_text(encoding="utf-8")
    )

    if not isinstance(result, dict):
        raise ValueError(
            "El contenido del resultado debe ser un diccionario JSON"
        )

    for section in ("snapshots", "events", "federated_rounds"):
        if section not in result:
            raise ValueError(
                f"El resultado no contiene la sección {section}"
            )

        if not isinstance(result[section], list):
            raise ValueError(
                f"La sección {section} debe ser una lista"
            )

    return result


def result_scenario_name(result: Mapping[str, Any]) -> str:
    """Obtiene el nombre del escenario desde summary o scenario."""

    summary = result.get("summary")

    if isinstance(summary, Mapping) and summary.get("scenario"):
        return str(summary["scenario"])

    scenario = result.get("scenario")

    if isinstance(scenario, Mapping) and scenario.get("name"):
        return str(scenario["name"])

    return "ESCENARIO"


def _round_status(round_record: Mapping[str, Any]) -> str:
    """Normaliza el estado de una ronda federada."""

    explicit_status = _first_present(
        round_record,
        ("status", "state", "result"),
    )

    if explicit_status is not None:
        status = str(explicit_status).upper()

        if any(token in status for token in ("CANCEL", "FAIL", "ABORT")):
            return "CANCELADA"

        if any(token in status for token in ("COMP", "SUCCESS", "OK")):
            return "COMPLETADA"

        return status

    if bool(round_record.get("cancelled", False)):
        return "CANCELADA"

    if "completed" in round_record:
        return (
            "COMPLETADA"
            if bool(round_record["completed"])
            else "CANCELADA"
        )

    return "COMPLETADA"


def normalize_federated_rounds(
    result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Normaliza las rondas FedAvg a una estructura común."""

    rounds = result.get("federated_rounds", [])

    if not isinstance(rounds, list):
        raise ValueError("federated_rounds debe ser una lista")

    normalized: list[dict[str, Any]] = []

    for position, round_record in enumerate(rounds, start=1):
        if not isinstance(round_record, Mapping):
            raise ValueError(
                "Cada ronda federada debe ser un diccionario"
            )

        round_index = int(
            _first_present(
                round_record,
                ROUND_INDEX_KEYS,
                position,
            )
        )

        loss_value = _first_present(
            round_record,
            LOSS_KEYS,
        )

        accuracy_value = _first_present(
            round_record,
            ACCURACY_KEYS,
        )

        participant_value = _first_present(
            round_record,
            PARTICIPANT_KEYS,
        )

        excluded_value = _first_present(
            round_record,
            EXCLUDED_KEYS,
        )

        normalized.append(
            {
                "round_index": round_index,
                "time_min": _time_min(
                    round_record,
                    fallback=float(round_index),
                ),
                "status": _round_status(round_record),
                "global_loss": (
                    None
                    if loss_value is None
                    else float(loss_value)
                ),
                "global_accuracy": (
                    None
                    if accuracy_value is None
                    else float(accuracy_value)
                ),
                "participant_count": _count_items(
                    participant_value
                ),
                "excluded_count": _count_items(
                    excluded_value
                ),
            }
        )

    normalized.sort(
        key=lambda item: (
            item["round_index"],
            item["time_min"],
        )
    )

    return normalized


def _extract_action(snapshot: Mapping[str, Any]) -> str:
    """Extrae la acción del supervisor desde campos planos o anidados."""

    value = _first_present(snapshot, ACTION_KEYS)

    if isinstance(value, Mapping):
        nested = _first_present(
            value,
            (
                "action",
                "name",
                "decision",
                "selected_action",
            ),
        )

        if nested is not None:
            value = nested

    if value is None:
        supervisor = snapshot.get("supervisor")

        if isinstance(supervisor, Mapping):
            value = _first_present(
                supervisor,
                ACTION_KEYS,
            )

    if value is None:
        return "SIN_REGISTRO"

    return str(value).strip().upper() or "SIN_REGISTRO"


def cognitive_decision_counts(
    result: Mapping[str, Any],
) -> dict[str, int]:
    """Cuenta las acciones cognitivas registradas en los snapshots."""

    snapshots = result.get("snapshots", [])

    if not isinstance(snapshots, list):
        raise ValueError("snapshots debe ser una lista")

    counter: Counter[str] = Counter()

    for snapshot in snapshots:
        if not isinstance(snapshot, Mapping):
            continue

        counter[_extract_action(snapshot)] += 1

    if not counter:
        counter["SIN_REGISTRO"] = 1

    return dict(counter)


def normalize_events(
    result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Normaliza eventos de escenario, supervisor y FedAvg."""

    raw_events = result.get("events", [])

    if not isinstance(raw_events, list):
        raise ValueError("events debe ser una lista")

    events: list[dict[str, Any]] = []

    for position, event in enumerate(raw_events):
        if not isinstance(event, Mapping):
            continue

        category = str(
            event.get("category", "SISTEMA")
        ).upper()

        effect = str(
            _first_present(
                event,
                ("effect", "event", "action", "type"),
                "EVENTO",
            )
        ).upper()

        transition = str(
            event.get("transition", "")
        ).upper()

        satellite_id = str(
            event.get("satellite_id", "")
        )

        label_parts = [effect, transition, satellite_id]
        label = " ".join(
            part for part in label_parts if part
        )

        events.append(
            {
                "time_min": _time_min(
                    event,
                    fallback=float(position),
                ),
                "category": category,
                "label": label,
                "message": str(
                    event.get("message", "")
                ),
            }
        )

    events.sort(
        key=lambda item: item["time_min"]
    )

    return events


def plot_fedavg_learning(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica pérdida y exactitud global por ronda FedAvg."""

    rounds = normalize_federated_rounds(result)
    scenario_name = result_scenario_name(result)

    figure, loss_axis = plt.subplots(figsize=(12, 6.5))
    accuracy_axis = loss_axis.twinx()

    completed_rounds = [
        item for item in rounds
        if item["status"] == "COMPLETADA"
    ]

    round_numbers = [
        item["round_index"]
        for item in completed_rounds
    ]

    losses = [
        item["global_loss"]
        for item in completed_rounds
        if item["global_loss"] is not None
    ]

    loss_rounds = [
        item["round_index"]
        for item in completed_rounds
        if item["global_loss"] is not None
    ]

    accuracies = [
        item["global_accuracy"] * 100.0
        for item in completed_rounds
        if item["global_accuracy"] is not None
    ]

    accuracy_rounds = [
        item["round_index"]
        for item in completed_rounds
        if item["global_accuracy"] is not None
    ]

    if losses:
        loss_axis.plot(
            loss_rounds,
            losses,
            marker="o",
            linewidth=2.0,
            label="Pérdida global",
        )

    if accuracies:
        accuracy_axis.plot(
            accuracy_rounds,
            accuracies,
            marker="s",
            linewidth=2.0,
            label="Exactitud global",
        )

    cancelled_rounds = [
        item["round_index"]
        for item in rounds
        if item["status"] == "CANCELADA"
    ]

    for round_index in cancelled_rounds:
        loss_axis.axvline(
            round_index,
            linestyle="--",
            alpha=0.35,
        )

    if not losses and not accuracies:
        loss_axis.text(
            0.5,
            0.5,
            "No se registraron métricas numéricas FedAvg",
            transform=loss_axis.transAxes,
            ha="center",
            va="center",
        )

    loss_axis.set_title(
        "Aprendizaje federado FedAvg\n"
        f"Escenario: {scenario_name}"
    )
    loss_axis.set_xlabel("Ronda federada")
    loss_axis.set_ylabel("Pérdida global")
    accuracy_axis.set_ylabel("Exactitud global [%]")
    accuracy_axis.set_ylim(0.0, 105.0)
    loss_axis.grid(alpha=0.30)

    handles_1, labels_1 = loss_axis.get_legend_handles_labels()
    handles_2, labels_2 = accuracy_axis.get_legend_handles_labels()

    if handles_1 or handles_2:
        loss_axis.legend(
            handles_1 + handles_2,
            labels_1 + labels_2,
            loc="best",
        )

    if rounds and not round_numbers:
        loss_axis.set_xticks(
            [item["round_index"] for item in rounds]
        )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem="01_fedavg_perdida_exactitud",
    )


def plot_fedavg_participation(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica participantes, exclusiones y estado de cada ronda."""

    rounds = normalize_federated_rounds(result)
    scenario_name = result_scenario_name(result)

    round_numbers = [
        item["round_index"] for item in rounds
    ]
    participants = [
        item["participant_count"] for item in rounds
    ]
    excluded = [
        item["excluded_count"] for item in rounds
    ]

    figure, axis = plt.subplots(figsize=(12, 6.5))

    axis.bar(
        round_numbers,
        participants,
        label="Participantes",
    )
    axis.bar(
        round_numbers,
        excluded,
        bottom=participants,
        label="Excluidos",
    )

    maximum_count = max(
        participants + excluded + [1]
    )

    for item in rounds:
        status = item["status"]
        axis.text(
            item["round_index"],
            maximum_count + 0.20,
            "OK" if status == "COMPLETADA" else "CANCELADA",
            ha="center",
            va="bottom",
            rotation=90 if status != "COMPLETADA" else 0,
            fontsize=8,
        )

    axis.set_title(
        "Participación en rondas FedAvg\n"
        f"Escenario: {scenario_name}"
    )
    axis.set_xlabel("Ronda federada")
    axis.set_ylabel("Número de satélites/clientes")
    axis.set_xticks(round_numbers)
    axis.set_ylim(0.0, maximum_count + 1.5)
    axis.grid(axis="y", alpha=0.30)
    axis.legend(loc="best")
    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem="02_fedavg_participacion",
    )


def plot_cognitive_decisions(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Grafica la distribución de acciones del supervisor cognitivo."""

    decision_counts = cognitive_decision_counts(result)
    scenario_name = result_scenario_name(result)

    ordered = sorted(
        decision_counts.items(),
        key=lambda item: (item[1], item[0]),
    )

    decisions = [item[0] for item in ordered]
    counts = [item[1] for item in ordered]

    figure, axis = plt.subplots(figsize=(12, 6.5))
    bars = axis.barh(decisions, counts)

    axis.set_title(
        "Distribución de decisiones del supervisor cognitivo\n"
        f"Escenario: {scenario_name}"
    )
    axis.set_xlabel("Número de decisiones registradas")
    axis.set_ylabel("Acción cognitiva")
    axis.grid(axis="x", alpha=0.30)

    for bar, count in zip(bars, counts):
        axis.text(
            count + max(counts + [1]) * 0.01,
            bar.get_y() + bar.get_height() / 2.0,
            str(count),
            va="center",
        )

    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem="03_decisiones_cognitivas",
    )


def plot_event_timeline(
    result: Mapping[str, Any],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Genera una línea temporal de eventos y fallas."""

    events = normalize_events(result)
    scenario_name = result_scenario_name(result)

    figure, axis = plt.subplots(figsize=(13, 7.0))

    if not events:
        axis.text(
            0.5,
            0.5,
            "No se registraron eventos",
            transform=axis.transAxes,
            ha="center",
            va="center",
        )
        axis.set_yticks([])
    else:
        categories = sorted(
            {event["category"] for event in events}
        )
        category_position = {
            category: index
            for index, category in enumerate(categories)
        }

        for event in events:
            y_position = category_position[event["category"]]
            axis.scatter(
                event["time_min"],
                y_position,
                s=55,
            )

            label = event["label"]
            if len(label) > 38:
                label = label[:35] + "..."

            axis.annotate(
                label,
                (
                    event["time_min"],
                    y_position,
                ),
                xytext=(4, 6),
                textcoords="offset points",
                rotation=30,
                fontsize=7,
            )

        axis.set_yticks(
            list(category_position.values()),
            labels=categories,
        )

    axis.set_title(
        "Línea temporal de eventos del sistema\n"
        f"Escenario: {scenario_name}"
    )
    axis.set_xlabel("Tiempo de simulación [min]")
    axis.set_ylabel("Categoría del evento")
    axis.grid(alpha=0.30)
    figure.tight_layout()

    return save_figure_bundle(
        figure=figure,
        output_directory=output_directory,
        filename_stem="04_linea_tiempo_eventos",
    )


def generate_intelligence_charts_for_scenario(
    result_path: str | Path,
    output_directory: str | Path,
) -> dict[str, dict[str, Path]]:
    """Genera las cuatro figuras de inteligencia de un escenario."""

    result = load_scenario_result(result_path)

    return {
        "fedavg_learning": plot_fedavg_learning(
            result,
            output_directory,
        ),
        "fedavg_participation": plot_fedavg_participation(
            result,
            output_directory,
        ),
        "cognitive_decisions": plot_cognitive_decisions(
            result,
            output_directory,
        ),
        "event_timeline": plot_event_timeline(
            result,
            output_directory,
        ),
    }


def generate_all_intelligence_charts(
    results_directory: str | Path,
    output_directory: str | Path,
) -> dict[str, dict[str, dict[str, Path]]]:
    """Genera el paquete de inteligencia para los ocho escenarios."""

    results_path = Path(results_directory)
    output_path = Path(output_directory)

    campaign: dict[
        str,
        dict[str, dict[str, Path]],
    ] = {}

    for scenario in ScenarioName:
        result_path = (
            results_path
            / f"{scenario.value.lower()}.json"
        )
        scenario_output = (
            output_path
            / scenario.value.lower()
        )

        campaign[scenario.value] = (
            generate_intelligence_charts_for_scenario(
                result_path=result_path,
                output_directory=scenario_output,
            )
        )

    return campaign
