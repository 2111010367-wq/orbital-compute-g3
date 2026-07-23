"""Catálogo de escenarios nominales y de falla del proyecto G3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from orbital_compute import config_g3


class ScenarioName(str, Enum):
    """Escenarios disponibles para la campaña de simulación."""

    NOMINAL = "NOMINAL"
    LOW_POWER = "LOW_POWER"
    ISL_DEGRADATION = "ISL_DEGRADATION"
    ISL_BLACKOUT = "ISL_BLACKOUT"
    SATELLITE_FAILURE = "SATELLITE_FAILURE"
    FORMATION_DISTURBANCE = "FORMATION_DISTURBANCE"
    FEDERATED_EXCLUSION = "FEDERATED_EXCLUSION"
    COMBINED_FAILURE = "COMBINED_FAILURE"


class ScenarioEffect(str, Enum):
    """Efectos que pueden inyectarse en el simulador integrado."""

    SET_SOC = "SET_SOC"
    ADD_POSITION_OFFSET = "ADD_POSITION_OFFSET"
    ADD_LINK_LOSS_DB = "ADD_LINK_LOSS_DB"
    FORCE_LINK_DOWN = "FORCE_LINK_DOWN"
    DISABLE_SATELLITE = "DISABLE_SATELLITE"
    EXCLUDE_FROM_FEDAVG = "EXCLUDE_FROM_FEDAVG"


ScalarOrVector = (
    float
    | tuple[float, float, float]
    | None
)


@dataclass(frozen=True)
class ScenarioEvent:
    """Evento de falla programado dentro de un escenario."""

    effect: ScenarioEffect
    start_time_s: float
    satellite_id: str
    duration_s: float | None = 0.0
    value: ScalarOrVector = None
    description: str = ""

    def __post_init__(self) -> None:
        """Valida los parámetros del evento."""

        if not isfinite(self.start_time_s):
            raise ValueError(
                "start_time_s debe ser un valor finito"
            )

        if self.start_time_s < 0.0:
            raise ValueError(
                "start_time_s no puede ser negativo"
            )

        if self.duration_s is not None:
            if not isfinite(self.duration_s):
                raise ValueError(
                    "duration_s debe ser finito o None"
                )

            if self.duration_s < 0.0:
                raise ValueError(
                    "duration_s no puede ser negativo"
                )

        if (
            self.satellite_id
            not in config_g3.SATELLITE_IDS
        ):
            raise ValueError(
                "satellite_id no pertenece "
                "a la formación G3"
            )

        if self.effect == ScenarioEffect.SET_SOC:
            if not isinstance(
                self.value,
                (int, float),
            ):
                raise ValueError(
                    "SET_SOC requiere un valor escalar"
                )

            if not 0.0 <= float(self.value) <= 1.0:
                raise ValueError(
                    "El SOC objetivo debe pertenecer "
                    "al intervalo [0, 1]"
                )

        elif (
            self.effect
            == ScenarioEffect.ADD_LINK_LOSS_DB
        ):
            if not isinstance(
                self.value,
                (int, float),
            ):
                raise ValueError(
                    "ADD_LINK_LOSS_DB requiere "
                    "un valor escalar"
                )

            if float(self.value) < 0.0:
                raise ValueError(
                    "La pérdida RF adicional "
                    "no puede ser negativa"
                )

        elif (
            self.effect
            == ScenarioEffect.ADD_POSITION_OFFSET
        ):
            if not isinstance(
                self.value,
                tuple,
            ):
                raise ValueError(
                    "ADD_POSITION_OFFSET requiere "
                    "una tupla tridimensional"
                )

            if len(self.value) != 3:
                raise ValueError(
                    "El desplazamiento debe tener "
                    "tres componentes"
                )

            if not all(
                isinstance(
                    component,
                    (int, float),
                )
                and isfinite(
                    float(component)
                )
                for component in self.value
            ):
                raise ValueError(
                    "El desplazamiento debe contener "
                    "valores finitos"
                )

        elif self.value is not None:
            raise ValueError(
                f"{self.effect.value} "
                "no requiere value"
            )

    @property
    def end_time_s(self) -> float | None:
        """Devuelve el instante final del evento."""

        if self.duration_s is None:
            return None

        return (
            self.start_time_s
            + self.duration_s
        )

    @property
    def is_instantaneous(self) -> bool:
        """Indica si el evento ocurre una sola vez."""

        return self.duration_s == 0.0

    def is_active(
        self,
        time_s: float,
    ) -> bool:
        """Determina si el efecto está activo."""

        if time_s < self.start_time_s:
            return False

        if self.duration_s is None:
            return True

        if self.is_instantaneous:
            return (
                time_s
                == self.start_time_s
            )

        return (
            time_s
            < self.start_time_s
            + self.duration_s
        )


@dataclass(frozen=True)
class ScenarioDefinition:
    """Definición completa de un escenario."""

    name: ScenarioName
    description: str
    events: tuple[
        ScenarioEvent,
        ...,
    ] = tuple()

    def __post_init__(self) -> None:
        """Valida la definición del escenario."""

        if not self.description.strip():
            raise ValueError(
                "La descripción del escenario "
                "no puede estar vacía"
            )

        ordered_events = tuple(
            sorted(
                self.events,
                key=lambda event: (
                    event.start_time_s
                ),
            )
        )

        if ordered_events != self.events:
            raise ValueError(
                "Los eventos deben estar "
                "ordenados por tiempo"
            )

    @property
    def is_nominal(self) -> bool:
        """Indica si el escenario no tiene fallas."""

        return (
            self.name
            == ScenarioName.NOMINAL
        )


SCENARIO_CATALOG: dict[
    ScenarioName,
    ScenarioDefinition,
] = {
    # ========================================================
    # ESCENARIO 1: OPERACIÓN NOMINAL
    # ========================================================

    ScenarioName.NOMINAL: ScenarioDefinition(
        name=ScenarioName.NOMINAL,
        description=(
            "Operación normal de los tres satélites "
            "sin fallas inyectadas."
        ),
    ),

    # ========================================================
    # ESCENARIO 2: ENERGÍA BAJA
    # ========================================================

    ScenarioName.LOW_POWER: ScenarioDefinition(
        name=ScenarioName.LOW_POWER,
        description=(
            "Descenso súbito del SOC de SAT-002 "
            "para evaluar la protección energética "
            "y su exclusión de FedAvg."
        ),
        events=(
            ScenarioEvent(
                effect=(
                    ScenarioEffect.SET_SOC
                ),
                start_time_s=900.0,
                satellite_id=(
                    config_g3.FOLLOWER_2_ID
                ),
                value=0.18,
                description=(
                    "SOC de SAT-002 reducido "
                    "a nivel crítico."
                ),
            ),
        ),
    ),

    # ========================================================
    # ESCENARIO 3: ENLACE KA DEGRADADO
    # ========================================================

    ScenarioName.ISL_DEGRADATION: (
        ScenarioDefinition(
            name=(
                ScenarioName.ISL_DEGRADATION
            ),
            description=(
                "Pérdida RF adicional temporal "
                "en el enlace de SAT-001."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .ADD_LINK_LOSS_DB
                    ),
                    start_time_s=900.0,
                    duration_s=900.0,
                    satellite_id=(
                        config_g3.FOLLOWER_1_ID
                    ),
                    value=35.0,
                    description=(
                        "Atenuación adicional "
                        "de 35 dB."
                    ),
                ),
            ),
        )
    ),

    # ========================================================
    # ESCENARIO 4: BLACKOUT DE COMUNICACIONES
    # ========================================================

    ScenarioName.ISL_BLACKOUT: (
        ScenarioDefinition(
            name=ScenarioName.ISL_BLACKOUT,
            description=(
                "Interrupción completa y temporal "
                "del enlace Ka de SAT-002."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .FORCE_LINK_DOWN
                    ),
                    start_time_s=1200.0,
                    duration_s=600.0,
                    satellite_id=(
                        config_g3.FOLLOWER_2_ID
                    ),
                    description=(
                        "Blackout Ka durante "
                        "diez minutos."
                    ),
                ),
            ),
        )
    ),

    # ========================================================
    # ESCENARIO 5: FALLA COMPLETA DE SATÉLITE
    # ========================================================

    ScenarioName.SATELLITE_FAILURE: (
        ScenarioDefinition(
            name=(
                ScenarioName
                .SATELLITE_FAILURE
            ),
            description=(
                "Falla permanente de SAT-002 "
                "durante la simulación."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .DISABLE_SATELLITE
                    ),
                    start_time_s=1800.0,
                    duration_s=None,
                    satellite_id=(
                        config_g3.FOLLOWER_2_ID
                    ),
                    description=(
                        "SAT-002 queda fuera "
                        "de servicio."
                    ),
                ),
            ),
        )
    ),

    # ========================================================
    # ESCENARIO 6: PERTURBACIÓN DE FORMACIÓN
    # ========================================================

    ScenarioName.FORMATION_DISTURBANCE: (
        ScenarioDefinition(
            name=(
                ScenarioName
                .FORMATION_DISTURBANCE
            ),
            description=(
                "Perturbación impulsiva de posición "
                "aplicada a SAT-001."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .ADD_POSITION_OFFSET
                    ),
                    start_time_s=1200.0,
                    satellite_id=(
                        config_g3.FOLLOWER_1_ID
                    ),
                    value=(
                        80.0,
                        -120.0,
                        40.0,
                    ),
                    description=(
                        "Desplazamiento impulsivo "
                        "en el marco LVLH."
                    ),
                ),
            ),
        )
    ),

    # ========================================================
    # ESCENARIO 7: EXCLUSIÓN DE FEDAVG
    # ========================================================

    ScenarioName.FEDERATED_EXCLUSION: (
        ScenarioDefinition(
            name=(
                ScenarioName
                .FEDERATED_EXCLUSION
            ),
            description=(
                "SAT-001 queda excluido "
                "temporalmente de las rondas FedAvg."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .EXCLUDE_FROM_FEDAVG
                    ),
                    start_time_s=600.0,
                    duration_s=1800.0,
                    satellite_id=(
                        config_g3.FOLLOWER_1_ID
                    ),
                    description=(
                        "Exclusión de FedAvg "
                        "durante treinta minutos."
                    ),
                ),
            ),
        )
    ),

    # ========================================================
    # ESCENARIO 8: FALLA COMBINADA
    # ========================================================

    ScenarioName.COMBINED_FAILURE: (
        ScenarioDefinition(
            name=(
                ScenarioName.COMBINED_FAILURE
            ),
            description=(
                "Combinación de perturbación "
                "de formación, pérdida RF "
                "y energía crítica."
            ),
            events=(
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .ADD_POSITION_OFFSET
                    ),
                    start_time_s=600.0,
                    satellite_id=(
                        config_g3.FOLLOWER_1_ID
                    ),
                    value=(
                        100.0,
                        150.0,
                        0.0,
                    ),
                    description=(
                        "Perturbación de formación "
                        "en SAT-001."
                    ),
                ),
                ScenarioEvent(
                    effect=(
                        ScenarioEffect
                        .ADD_LINK_LOSS_DB
                    ),
                    start_time_s=1200.0,
                    duration_s=900.0,
                    satellite_id=(
                        config_g3.FOLLOWER_1_ID
                    ),
                    value=35.0,
                    description=(
                        "Degradación temporal "
                        "del enlace de SAT-001."
                    ),
                ),
                ScenarioEvent(
                    effect=(
                        ScenarioEffect.SET_SOC
                    ),
                    start_time_s=1800.0,
                    satellite_id=(
                        config_g3.FOLLOWER_2_ID
                    ),
                    value=0.18,
                    description=(
                        "SOC crítico en SAT-002."
                    ),
                ),
            ),
        )
    ),
}


def get_scenario(
    scenario: ScenarioName | str,
) -> ScenarioDefinition:
    """Obtiene una definición por enum o texto."""

    try:
        scenario_name = ScenarioName(
            scenario
        )

    except ValueError as error:
        available = ", ".join(
            item.value
            for item in ScenarioName
        )

        raise ValueError(
            f"Escenario desconocido: {scenario}. "
            f"Disponibles: {available}"
        ) from error

    return SCENARIO_CATALOG[
        scenario_name
    ]


def list_scenarios(
) -> tuple[ScenarioDefinition, ...]:
    """Devuelve todos los escenarios disponibles."""

    return tuple(
        SCENARIO_CATALOG[
            scenario_name
        ]
        for scenario_name
        in ScenarioName
    )