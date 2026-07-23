"""
Motor temporal de escenarios nominales y de falla del proyecto G3.

Este módulo determina:

- Cuándo comienza una falla.
- Cuándo termina una falla temporal.
- Qué efectos están activos.
- Qué satélite está afectado.
- Cómo aplicar perturbaciones instantáneas.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from orbital_compute.energy_g3 import (
    CubeSatEnergySystem,
)
from orbital_compute.scenarios_g3 import (
    ScenarioDefinition,
    ScenarioEffect,
)


class ScenarioRuntime:
    """Gestiona la ejecución temporal de un escenario."""

    def __init__(
        self,
        scenario: ScenarioDefinition,
    ) -> None:
        self.scenario = scenario

        self._started_events: set[int] = set()

        self._finished_events: set[int] = set()

    def update(
        self,
        time_s: float,
        relative_states: dict[
            str,
            np.ndarray,
        ],
        energy_systems: dict[
            str,
            CubeSatEnergySystem,
        ],
    ) -> list[dict[str, Any]]:
        """
        Actualiza el escenario en un instante determinado.

        Los efectos instantáneos, como modificar el SOC o
        desplazar la posición de un satélite, se aplican una
        única vez.

        También genera eventos de inicio y finalización.
        """

        emitted_events: list[
            dict[str, Any]
        ] = []

        for (
            event_index,
            event,
        ) in enumerate(
            self.scenario.events
        ):
            # =============================================
            # INICIO DEL EVENTO
            # =============================================

            if (
                time_s
                >= event.start_time_s
                and event_index
                not in self._started_events
            ):
                self._started_events.add(
                    event_index
                )

                # Reducción instantánea de energía
                if (
                    event.effect
                    == ScenarioEffect.SET_SOC
                ):
                    energy_system = (
                        energy_systems[
                            event.satellite_id
                        ]
                    )

                    target_soc = float(
                        event.value
                    )

                    energy_system.battery_energy_wh = (
                        target_soc
                        * energy_system
                        .battery_capacity_wh
                    )

                # Perturbación instantánea de posición
                elif (
                    event.effect
                    == ScenarioEffect
                    .ADD_POSITION_OFFSET
                ):
                    offset_m = np.asarray(
                        event.value,
                        dtype=float,
                    )

                    relative_states[
                        event.satellite_id
                    ][0:3] += offset_m

                emitted_events.append(
                    {
                        "time_s": float(
                            time_s
                        ),
                        "time_min": float(
                            time_s / 60.0
                        ),
                        "category": (
                            "ESCENARIO"
                        ),
                        "scenario": (
                            self.scenario
                            .name.value
                        ),
                        "effect": (
                            event.effect.value
                        ),
                        "satellite_id": (
                            event.satellite_id
                        ),
                        "transition": (
                            "INICIO"
                        ),
                        "message": (
                            event.description
                            or event.effect.value
                        ),
                    }
                )

            # =============================================
            # FINAL DEL EVENTO TEMPORAL
            # =============================================

            end_time_s = event.end_time_s

            if (
                end_time_s is not None
                and event.duration_s is not None
                and event.duration_s > 0.0
                and time_s >= end_time_s
                and event_index
                not in self._finished_events
            ):
                self._finished_events.add(
                    event_index
                )

                emitted_events.append(
                    {
                        "time_s": float(
                            time_s
                        ),
                        "time_min": float(
                            time_s / 60.0
                        ),
                        "category": (
                            "ESCENARIO"
                        ),
                        "scenario": (
                            self.scenario
                            .name.value
                        ),
                        "effect": (
                            event.effect.value
                        ),
                        "satellite_id": (
                            event.satellite_id
                        ),
                        "transition": (
                            "FIN"
                        ),
                        "message": (
                            "Finaliza: "
                            f"{event.description}"
                        ),
                    }
                )

        return emitted_events

    def active_effects(
        self,
        satellite_id: str,
        time_s: float,
    ) -> tuple[str, ...]:
        """Devuelve los efectos activos en un satélite."""

        return tuple(
            event.effect.value
            for event in self.scenario.events
            if (
                event.satellite_id
                == satellite_id
                and not event.is_instantaneous
                and event.is_active(
                    time_s
                )
            )
        )

    def additional_link_loss_db(
        self,
        satellite_id: str,
        time_s: float,
    ) -> float:
        """Calcula la pérdida RF adicional activa."""

        return float(
            sum(
                float(event.value)
                for event
                in self.scenario.events
                if (
                    event.satellite_id
                    == satellite_id
                    and event.effect
                    == ScenarioEffect
                    .ADD_LINK_LOSS_DB
                    and event.is_active(
                        time_s
                    )
                )
            )
        )

    def link_forced_down(
        self,
        satellite_id: str,
        time_s: float,
    ) -> bool:
        """Indica si existe blackout de comunicación."""

        return any(
            event.satellite_id
            == satellite_id
            and event.effect
            == ScenarioEffect.FORCE_LINK_DOWN
            and event.is_active(
                time_s
            )
            for event
            in self.scenario.events
        )

    def satellite_disabled(
        self,
        satellite_id: str,
        time_s: float,
    ) -> bool:
        """Indica si el satélite está fuera de servicio."""

        return any(
            event.satellite_id
            == satellite_id
            and event.effect
            == ScenarioEffect.DISABLE_SATELLITE
            and event.is_active(
                time_s
            )
            for event
            in self.scenario.events
        )

    def federated_excluded(
        self,
        satellite_id: str,
        time_s: float,
    ) -> bool:
        """Indica si el nodo está excluido de FedAvg."""

        return any(
            event.satellite_id
            == satellite_id
            and event.effect
            == ScenarioEffect
            .EXCLUDE_FROM_FEDAVG
            and event.is_active(
                time_s
            )
            for event
            in self.scenario.events
        )