"""
Supervisor cognitivo del proyecto G3.

Integra decisiones basadas en:

- Estado energético.
- Error de formación.
- Temperatura.
- Disponibilidad y margen del enlace Ka.
- Solicitud de aprendizaje federado.

Las funciones críticas de seguridad y control tienen prioridad
sobre las tareas de inteligencia artificial.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from orbital_compute import config_g3
from orbital_compute.energy_g3 import OperatingMode


class CognitiveAction(str, Enum):
    """Acción principal seleccionada para un satélite."""

    NOMINAL = "OPERACION_NOMINAL"
    RECOVER_FORMATION = "RECUPERAR_FORMACION"
    POWER_SAVE = "AHORRO_ENERGIA"
    CRITICAL_POWER = "ENERGIA_CRITICA"
    LINK_DEGRADED = "ENLACE_DEGRADADO"
    THERMAL_PROTECTION = "PROTECCION_TERMICA"
    THERMAL_CRITICAL = "TEMPERATURA_CRITICA"


@dataclass(frozen=True)
class SatelliteCognitiveState:
    """Estado observado por el supervisor."""

    satellite_id: str
    soc: float
    energy_mode: OperatingMode

    temperature_c: float
    formation_error_m: float

    link_margin_db: float
    link_available: bool

    training_requested: bool = True


@dataclass(frozen=True)
class SupervisorDecision:
    """Decisión cognitiva para un satélite."""

    satellite_id: str
    action: CognitiveAction
    priority: int
    reason: str

    control_active: bool
    isl_control_channel_active: bool
    noncritical_communications_allowed: bool
    federated_training_allowed: bool


@dataclass(frozen=True)
class FleetDecision:
    """Resultado de la evaluación completa de la formación."""

    satellite_decisions: tuple[SupervisorDecision, ...]
    eligible_federated_clients: tuple[str, ...]
    excluded_federated_clients: tuple[str, ...]
    federated_round_allowed: bool
    minimum_required_participants: int


class CognitiveSupervisor:
    """Supervisor de decisiones para la formación G3."""

    def __init__(
        self,
        minimum_soc: float = config_g3.MINIMUM_SOC,
        critical_soc: float = config_g3.CRITICAL_SOC,
        maximum_formation_error_m: float = (
            config_g3.MAX_FORMATION_ERROR_M
        ),
        minimum_link_margin_db: float = 0.0,
        maximum_temperature_c: float = (
            config_g3.MAX_OPERATION_TEMPERATURE_C
        ),
        critical_temperature_c: float = (
            config_g3.CRITICAL_TEMPERATURE_C
        ),
        minimum_federated_participants: int = (
            config_g3.MIN_FEDERATED_PARTICIPANTS
        ),
    ) -> None:
        if not 0.0 <= critical_soc < minimum_soc <= 1.0:
            raise ValueError(
                "Deben cumplirse 0 <= critical_soc < minimum_soc <= 1"
            )

        if maximum_formation_error_m <= 0.0:
            raise ValueError(
                "El error máximo de formación debe ser positivo"
            )

        if critical_temperature_c <= maximum_temperature_c:
            raise ValueError(
                "La temperatura crítica debe superar el límite normal"
            )

        if minimum_federated_participants <= 0:
            raise ValueError(
                "El número mínimo de participantes debe ser positivo"
            )

        self.minimum_soc = minimum_soc
        self.critical_soc = critical_soc
        self.maximum_formation_error_m = (
            maximum_formation_error_m
        )
        self.minimum_link_margin_db = minimum_link_margin_db
        self.maximum_temperature_c = maximum_temperature_c
        self.critical_temperature_c = critical_temperature_c
        self.minimum_federated_participants = (
            minimum_federated_participants
        )

    @staticmethod
    def _validate_state(
        state: SatelliteCognitiveState,
    ) -> None:
        """Valida las variables recibidas por el supervisor."""

        if not state.satellite_id:
            raise ValueError(
                "satellite_id no puede estar vacío"
            )

        if not 0.0 <= state.soc <= 1.0:
            raise ValueError(
                "El SOC debe pertenecer al intervalo [0, 1]"
            )

        numeric_values = {
            "temperature_c": state.temperature_c,
            "formation_error_m": state.formation_error_m,
            "link_margin_db": state.link_margin_db,
        }

        for name, value in numeric_values.items():
            if not isfinite(value):
                raise ValueError(
                    f"{name} debe ser un valor finito"
                )

        if state.formation_error_m < 0.0:
            raise ValueError(
                "El error de formación no puede ser negativo"
            )

    def decide(
        self,
        state: SatelliteCognitiveState,
    ) -> SupervisorDecision:
        """Selecciona la acción principal para un satélite."""

        self._validate_state(state)

        essential_isl_available = state.link_available

        # Prioridad 1: protección térmica crítica.
        if state.temperature_c >= self.critical_temperature_c:
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.THERMAL_CRITICAL,
                priority=1,
                reason=(
                    "Temperatura crítica: se suspenden todas las "
                    "cargas no esenciales"
                ),
                control_active=True,
                isl_control_channel_active=essential_isl_available,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Prioridad 2: energía crítica.
        if (
            state.soc <= self.critical_soc
            or state.energy_mode == OperatingMode.CRITICAL
        ):
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.CRITICAL_POWER,
                priority=2,
                reason=(
                    "SOC crítico: se preservan únicamente funciones "
                    "de seguridad y control"
                ),
                control_active=True,
                isl_control_channel_active=essential_isl_available,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Prioridad 3: pérdida de formación.
        if (
            state.formation_error_m
            > self.maximum_formation_error_m
        ):
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.RECOVER_FORMATION,
                priority=3,
                reason=(
                    "Error de formación superior al límite: "
                    "se prioriza el controlador"
                ),
                control_active=True,
                isl_control_channel_active=essential_isl_available,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Prioridad 4: temperatura superior al límite operativo.
        if state.temperature_c >= self.maximum_temperature_c:
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.THERMAL_PROTECTION,
                priority=4,
                reason=(
                    "Temperatura elevada: se suspende el "
                    "entrenamiento federado"
                ),
                control_active=True,
                isl_control_channel_active=essential_isl_available,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Prioridad 5: ahorro energético.
        if (
            state.soc <= self.minimum_soc
            or state.energy_mode == OperatingMode.POWER_SAVE
        ):
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.POWER_SAVE,
                priority=5,
                reason=(
                    "SOC bajo: se desactivan las cargas "
                    "computacionales no críticas"
                ),
                control_active=True,
                isl_control_channel_active=essential_isl_available,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Prioridad 6: enlace insuficiente.
        if (
            not state.link_available
            or state.link_margin_db
            < self.minimum_link_margin_db
        ):
            return SupervisorDecision(
                satellite_id=state.satellite_id,
                action=CognitiveAction.LINK_DEGRADED,
                priority=6,
                reason=(
                    "Margen RF insuficiente o enlace no disponible"
                ),
                control_active=True,
                isl_control_channel_active=False,
                noncritical_communications_allowed=False,
                federated_training_allowed=False,
            )

        # Estado nominal.
        return SupervisorDecision(
            satellite_id=state.satellite_id,
            action=CognitiveAction.NOMINAL,
            priority=7,
            reason="Todos los parámetros se encuentran dentro de límites",
            control_active=True,
            isl_control_channel_active=True,
            noncritical_communications_allowed=True,
            federated_training_allowed=state.training_requested,
        )

    def evaluate_fleet(
        self,
        states: list[SatelliteCognitiveState],
    ) -> FleetDecision:
        """Evalúa todos los satélites y autoriza o cancela FedAvg."""

        if not states:
            raise ValueError(
                "Se requiere al menos un estado satelital"
            )

        decisions = tuple(
            self.decide(state)
            for state in states
        )

        eligible_clients = tuple(
            decision.satellite_id
            for decision in decisions
            if decision.federated_training_allowed
        )

        excluded_clients = tuple(
            decision.satellite_id
            for decision in decisions
            if not decision.federated_training_allowed
        )

        round_allowed = (
            len(eligible_clients)
            >= self.minimum_federated_participants
        )

        return FleetDecision(
            satellite_decisions=decisions,
            eligible_federated_clients=eligible_clients,
            excluded_federated_clients=excluded_clients,
            federated_round_allowed=round_allowed,
            minimum_required_participants=(
                self.minimum_federated_participants
            ),
        )