"""
Modelo energético para los tres CubeSats del proyecto G3.

Incluye:

- Generación solar.
- Consumo de subsistemas.
- Carga y descarga de batería.
- Eficiencias de carga y descarga.
- Estado de carga SOC.
- Modos normal, ahorro y crítico.
- Restricción energética para aprendizaje federado.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from orbital_compute import config_g3


class OperatingMode(str, Enum):
    """Estados operativos según el nivel de energía."""

    NORMAL = "NORMAL"
    POWER_SAVE = "AHORRO_ENERGIA"
    CRITICAL = "CRITICO"


@dataclass(frozen=True)
class EnergyLoads:
    """Configuración de los subsistemas activos."""

    housekeeping_active: bool = True
    control_active: bool = True
    isl_active: bool = False
    federated_training_active: bool = False

    def total_power_w(self) -> float:
        """Calcula el consumo eléctrico total."""

        power_w = 0.0

        if self.housekeeping_active:
            power_w += config_g3.HOUSEKEEPING_POWER_W

        if self.control_active:
            power_w += config_g3.CONTROL_SYSTEM_POWER_W

        if self.isl_active:
            power_w += config_g3.ISL_COMMUNICATION_POWER_W

        if self.federated_training_active:
            power_w += config_g3.FEDERATED_TRAINING_POWER_W

        return power_w


@dataclass(frozen=True)
class EnergyStepResult:
    """Resultado de un paso temporal del modelo energético."""

    time_step_s: float
    illuminated: bool

    solar_power_w: float
    load_power_w: float
    net_power_w: float

    battery_energy_wh: float
    soc: float
    mode: OperatingMode

    federated_training_allowed: bool
    battery_depleted: bool


@dataclass
class CubeSatEnergySystem:
    """Modelo de potencia y batería de un CubeSat."""

    battery_capacity_wh: float = config_g3.BATTERY_CAPACITY_WH
    initial_soc: float = config_g3.INITIAL_SOC
    solar_power_w: float = config_g3.SOLAR_POWER_W

    charge_efficiency: float = 0.90
    discharge_efficiency: float = 0.95

    minimum_soc: float = config_g3.MINIMUM_SOC
    critical_soc: float = config_g3.CRITICAL_SOC

    def __post_init__(self) -> None:
        if self.battery_capacity_wh <= 0.0:
            raise ValueError(
                "La capacidad de batería debe ser positiva"
            )

        if self.solar_power_w < 0.0:
            raise ValueError(
                "La potencia solar no puede ser negativa"
            )

        if not 0.0 <= self.initial_soc <= 1.0:
            raise ValueError(
                "El SOC inicial debe pertenecer al intervalo [0, 1]"
            )

        if not 0.0 < self.charge_efficiency <= 1.0:
            raise ValueError(
                "La eficiencia de carga debe estar en (0, 1]"
            )

        if not 0.0 < self.discharge_efficiency <= 1.0:
            raise ValueError(
                "La eficiencia de descarga debe estar en (0, 1]"
            )

        if not 0.0 <= self.critical_soc < self.minimum_soc <= 1.0:
            raise ValueError(
                "Deben cumplirse 0 <= critical_soc < minimum_soc <= 1"
            )

        self.battery_energy_wh = (
            self.initial_soc * self.battery_capacity_wh
        )

    @property
    def soc(self) -> float:
        """Estado de carga normalizado entre cero y uno."""

        return self.battery_energy_wh / self.battery_capacity_wh

    @property
    def mode(self) -> OperatingMode:
        """Determina el modo energético actual."""

        if self.soc <= self.critical_soc:
            return OperatingMode.CRITICAL

        if self.soc <= self.minimum_soc:
            return OperatingMode.POWER_SAVE

        return OperatingMode.NORMAL

    def federated_training_allowed(self) -> bool:
        """
        Permite entrenamiento únicamente en modo normal.

        El control de formación y las funciones básicas tienen
        prioridad sobre la carga computacional federada.
        """

        return self.mode == OperatingMode.NORMAL

    def step(
        self,
        time_step_s: float,
        illuminated: bool,
        loads: EnergyLoads,
    ) -> EnergyStepResult:
        """
        Actualiza la batería durante un paso temporal.

        Parameters
        ----------
        time_step_s:
            Duración del paso en segundos.
        illuminated:
            Verdadero cuando el satélite recibe energía solar.
        loads:
            Subsistemas activos durante el paso.

        Returns
        -------
        EnergyStepResult
            Estado energético después del paso.
        """

        if time_step_s <= 0.0:
            raise ValueError(
                "El paso temporal debe ser positivo"
            )

        solar_generation_w = (
            self.solar_power_w if illuminated else 0.0
        )

        load_power_w = loads.total_power_w()
        net_power_w = solar_generation_w - load_power_w

        time_step_h = time_step_s / 3600.0

        if net_power_w >= 0.0:
            energy_change_wh = (
                net_power_w
                * self.charge_efficiency
                * time_step_h
            )
        else:
            energy_change_wh = (
                net_power_w
                / self.discharge_efficiency
                * time_step_h
            )

        self.battery_energy_wh += energy_change_wh

        self.battery_energy_wh = min(
            max(self.battery_energy_wh, 0.0),
            self.battery_capacity_wh,
        )

        training_allowed = self.federated_training_allowed()

        return EnergyStepResult(
            time_step_s=time_step_s,
            illuminated=illuminated,
            solar_power_w=solar_generation_w,
            load_power_w=load_power_w,
            net_power_w=net_power_w,
            battery_energy_wh=self.battery_energy_wh,
            soc=self.soc,
            mode=self.mode,
            federated_training_allowed=training_allowed,
            battery_depleted=self.battery_energy_wh <= 0.0,
        )