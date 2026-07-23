"""
Demostración del supervisor cognitivo del proyecto G3.

El supervisor evalúa el estado energético, térmico,
de formación y de comunicaciones de tres CubeSats,
y decide si pueden participar en una ronda FedAvg.
"""

from orbital_compute.cognitive_supervisor_g3 import (
    CognitiveSupervisor,
    SatelliteCognitiveState,
)
from orbital_compute.energy_g3 import OperatingMode


def main() -> None:
    """Ejecuta una demostración del supervisor cognitivo."""

    supervisor = CognitiveSupervisor()

    # =========================================================
    # ESTADOS DE LOS TRES SATÉLITES
    # =========================================================

    states = [
        SatelliteCognitiveState(
            satellite_id="SAT-000",
            soc=0.72,
            energy_mode=OperatingMode.NORMAL,
            temperature_c=27.0,
            formation_error_m=8.0,
            link_margin_db=25.0,
            link_available=True,
            training_requested=True,
        ),
        SatelliteCognitiveState(
            satellite_id="SAT-001",
            soc=0.61,
            energy_mode=OperatingMode.NORMAL,
            temperature_c=29.0,
            formation_error_m=125.0,
            link_margin_db=18.0,
            link_available=True,
            training_requested=True,
        ),
        SatelliteCognitiveState(
            satellite_id="SAT-002",
            soc=0.24,
            energy_mode=OperatingMode.POWER_SAVE,
            temperature_c=31.0,
            formation_error_m=12.0,
            link_margin_db=15.0,
            link_available=True,
            training_requested=True,
        ),
    ]

    # Evaluación conjunta de la formación
    result = supervisor.evaluate_fleet(states)

    # =========================================================
    # ENCABEZADO
    # =========================================================

    print("=" * 110)
    print("SUPERVISOR COGNITIVO DE LA FORMACIÓN SATELITAL — PROYECTO G3")
    print("=" * 110)

    # =========================================================
    # RESULTADO INDIVIDUAL DE CADA SATÉLITE
    # =========================================================

    for decision in result.satellite_decisions:
        control_state = (
            "SÍ"
            if decision.control_active
            else "NO"
        )

        isl_state = (
            "SÍ"
            if decision.isl_control_channel_active
            else "NO"
        )

        communication_state = (
            "SÍ"
            if decision.noncritical_communications_allowed
            else "NO"
        )

        fedavg_state = (
            "SÍ"
            if decision.federated_training_allowed
            else "NO"
        )

        print(
            f"{decision.satellite_id} | "
            f"Acción={decision.action.value:24} | "
            f"Prioridad={decision.priority} | "
            f"Control={control_state} | "
            f"ISL={isl_state} | "
            f"Com. no crítica={communication_state} | "
            f"FedAvg={fedavg_state}"
        )

        print(
            f"          Motivo: {decision.reason}"
        )

        print("-" * 110)

    # =========================================================
    # DECISIÓN GLOBAL DE APRENDIZAJE FEDERADO
    # =========================================================

    if result.eligible_federated_clients:
        eligible_text = ", ".join(
            result.eligible_federated_clients
        )
    else:
        eligible_text = "Ninguno"

    if result.excluded_federated_clients:
        excluded_text = ", ".join(
            result.excluded_federated_clients
        )
    else:
        excluded_text = "Ninguno"

    federated_round_state = (
        "AUTORIZADA"
        if result.federated_round_allowed
        else "CANCELADA"
    )

    print("RESUMEN GLOBAL")
    print("-" * 110)

    print(
        f"Clientes elegibles para FedAvg: {eligible_text}"
    )

    print(
        f"Clientes excluidos de FedAvg: {excluded_text}"
    )

    print(
        "Participantes mínimos requeridos: "
        f"{result.minimum_required_participants}"
    )

    print(
        f"Estado de la ronda FedAvg: {federated_round_state}"
    )

    print("=" * 110)


if __name__ == "__main__":
    main()