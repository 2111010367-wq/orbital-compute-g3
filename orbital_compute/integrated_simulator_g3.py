"""Simulador integrado del proyecto G3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from orbital_compute import config_g3
from orbital_compute.cognitive_supervisor_g3 import (
    CognitiveSupervisor,
    SatelliteCognitiveState,
)
from orbital_compute.energy_g3 import (
    CubeSatEnergySystem,
    EnergyLoads,
)
from orbital_compute.federated_real_g3 import (
    FederatedCoordinator,
    make_satellite_datasets,
)
from orbital_compute.formation_control import (
    FormationController,
    mean_motion_rad_s,
    rk4_step,
)
from orbital_compute.rf_isl_ka import RFISLKa


class IntegratedG3Simulator:
    """
    Simulador integrado de la arquitectura cognitiva G3.

    Integra:

    - Dinámica relativa HCW.
    - Control PD de formación.
    - Enlace inter-satélite en banda Ka.
    - Sistema energético.
    - Aprendizaje federado FedAvg.
    - Supervisor cognitivo.
    - Registro de eventos y resultados.
    """

    def __init__(
        self,
        duration_s: float = 3600.0,
        time_step_s: float = 60.0,
        federated_interval_s: float = 600.0,
        random_seed: int = 42,
    ) -> None:
        if duration_s <= 0.0:
            raise ValueError(
                "duration_s debe ser positivo"
            )

        if time_step_s <= 0.0:
            raise ValueError(
                "time_step_s debe ser positivo"
            )

        if federated_interval_s <= 0.0:
            raise ValueError(
                "federated_interval_s debe ser positivo"
            )

        duration_steps = duration_s / time_step_s

        federated_steps = (
            federated_interval_s / time_step_s
        )

        if not np.isclose(
            duration_steps,
            round(duration_steps),
        ):
            raise ValueError(
                "duration_s debe ser múltiplo "
                "de time_step_s"
            )

        if not np.isclose(
            federated_steps,
            round(federated_steps),
        ):
            raise ValueError(
                "federated_interval_s debe ser múltiplo "
                "de time_step_s"
            )

        self.duration_s = float(duration_s)

        self.time_step_s = float(time_step_s)

        self.number_of_steps = int(
            round(duration_steps)
        )

        self.federated_interval_steps = int(
            round(federated_steps)
        )

        self.satellite_ids = tuple(
            config_g3.SATELLITE_IDS
        )

        self.leader_id = config_g3.LEADER_ID

        if len(self.satellite_ids) != 3:
            raise ValueError(
                "La simulación integrada requiere "
                "exactamente tres satélites"
            )

        # =====================================================
        # POSICIONES DESEADAS EN EL SISTEMA LVLH
        # =====================================================

        self.desired_positions = {
            self.leader_id: np.array(
                [0.0, 0.0, 0.0],
                dtype=float,
            ),
            config_g3.FOLLOWER_1_ID: np.asarray(
                config_g3
                .FOLLOWER_1_DESIRED_POSITION_M,
                dtype=float,
            ),
            config_g3.FOLLOWER_2_ID: np.asarray(
                config_g3
                .FOLLOWER_2_DESIRED_POSITION_M,
                dtype=float,
            ),
        }

        # =====================================================
        # CONDICIONES INICIALES
        #
        # Estado:
        # [x, y, z, vx, vy, vz]
        # =====================================================

        self.relative_states = {
            self.leader_id: np.array(
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                dtype=float,
            ),
            config_g3.FOLLOWER_1_ID: np.array(
                [
                    0.0,
                    1200.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                dtype=float,
            ),
            config_g3.FOLLOWER_2_ID: np.array(
                [
                    0.0,
                    -1050.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                dtype=float,
            ),
        }

        # =====================================================
        # ESTADOS ENERGÉTICOS INICIALES
        # =====================================================

        self.energy_systems = {
            self.leader_id: CubeSatEnergySystem(
                initial_soc=0.80,
            ),
            config_g3.FOLLOWER_1_ID: (
                CubeSatEnergySystem(
                    initial_soc=0.65,
                )
            ),
            config_g3.FOLLOWER_2_ID: (
                CubeSatEnergySystem(
                    initial_soc=0.25,
                )
            ),
        }

        # Temperaturas iniciales
        self.temperatures_c = {
            self.leader_id: 26.0,
            config_g3.FOLLOWER_1_ID: 27.0,
            config_g3.FOLLOWER_2_ID: 28.0,
        }

        # =====================================================
        # SUBSISTEMAS
        # =====================================================

        self.formation_controller = (
            FormationController()
        )

        self.orbital_mean_motion = (
            mean_motion_rad_s()
        )

        self.rf_link = RFISLKa()

        self.cognitive_supervisor = (
            CognitiveSupervisor()
        )

        # =====================================================
        # APRENDIZAJE FEDERADO
        # =====================================================

        (
            clients,
            evaluation_features,
            evaluation_labels,
        ) = make_satellite_datasets(
            samples_per_client=120,
            evaluation_samples=300,
            random_seed=random_seed,
        )

        self.federated_coordinator = (
            FederatedCoordinator(
                clients=clients,
                evaluation_features=(
                    evaluation_features
                ),
                evaluation_labels=(
                    evaluation_labels
                ),
            )
        )

        self.initial_federated_metrics = (
            self.federated_coordinator
            .evaluate_global_model()
        )

    @staticmethod
    def is_illuminated(
        time_s: float,
    ) -> bool:
        """
        Modelo simplificado de iluminación.

        En cada ciclo de una hora:

        - 40 minutos de iluminación.
        - 20 minutos de eclipse.
        """

        cycle_time_s = time_s % 3600.0

        return cycle_time_s < 2400.0

    @staticmethod
    def vector_to_list(
        vector: np.ndarray,
    ) -> list[float]:
        """Convierte un vector NumPy en una lista JSON."""

        return [
            float(value)
            for value in vector
        ]

    def calculate_formation_errors(
        self,
    ) -> dict[str, float]:
        """Calcula el error de formación por satélite."""

        errors: dict[str, float] = {}

        for satellite_id in self.satellite_ids:
            position = self.relative_states[
                satellite_id
            ][0:3]

            desired_position = (
                self.desired_positions[satellite_id]
            )

            errors[satellite_id] = float(
                np.linalg.norm(
                    position - desired_position
                )
            )

        return errors

    def calculate_control_commands(
        self,
    ) -> dict[str, np.ndarray]:
        """Calcula la aceleración de control."""

        commands = {
            self.leader_id: np.zeros(
                3,
                dtype=float,
            )
        }

        for satellite_id in self.satellite_ids:
            if satellite_id == self.leader_id:
                continue

            state = self.relative_states[
                satellite_id
            ]

            commands[satellite_id] = (
                self.formation_controller.command(
                    position_m=state[0:3],
                    velocity_m_s=state[3:6],
                    desired_position_m=(
                        self.desired_positions[
                            satellite_id
                        ]
                    ),
                )
            )

        return commands

    def calculate_links(
        self,
    ) -> tuple[
        dict[str, Any],
        dict[str, float],
    ]:
        """
        Evalúa los enlaces líder-seguidor.

        Para el líder se utiliza el peor margen de sus
        dos enlaces con los seguidores.
        """

        link_results: dict[str, Any] = {}

        distances_km: dict[str, float] = {
            self.leader_id: 0.0
        }

        follower_results = []

        for satellite_id in self.satellite_ids:
            if satellite_id == self.leader_id:
                continue

            position = self.relative_states[
                satellite_id
            ][0:3]

            distance_km = max(
                float(
                    np.linalg.norm(position)
                )
                / 1000.0,
                1.0e-6,
            )

            result = self.rf_link.evaluate(
                distance_km=distance_km
            )

            link_results[satellite_id] = result

            distances_km[satellite_id] = (
                distance_km
            )

            follower_results.append(result)

        worst_link = min(
            follower_results,
            key=lambda result: (
                result.link_margin_db
            ),
        )

        link_results[self.leader_id] = (
            worst_link
        )

        return link_results, distances_km

    def run(self) -> dict[str, Any]:
        """Ejecuta la simulación integrada."""

        snapshots: list[dict[str, Any]] = []

        events: list[dict[str, Any]] = []

        federated_rounds: list[
            dict[str, Any]
        ] = []

        previous_actions: dict[str, str] = {}

        previous_illumination: bool | None = (
            None
        )

        cancelled_rounds = 0

        # =====================================================
        # BUCLE PRINCIPAL
        # =====================================================

        for step_index in range(
            self.number_of_steps + 1
        ):
            time_s = (
                step_index * self.time_step_s
            )

            illuminated = self.is_illuminated(
                time_s
            )

            federated_round_due = (
                step_index
                % self.federated_interval_steps
                == 0
            )

            # Cambio iluminación/eclipses
            if (
                illuminated
                != previous_illumination
            ):
                events.append(
                    {
                        "time_s": time_s,
                        "time_min": (
                            time_s / 60.0
                        ),
                        "category": "ORBITA",
                        "message": (
                            "Entrada en iluminación solar"
                            if illuminated
                            else "Entrada en eclipse"
                        ),
                    }
                )

                previous_illumination = (
                    illuminated
                )

            # Formación
            formation_errors = (
                self.calculate_formation_errors()
            )

            control_commands = (
                self.calculate_control_commands()
            )

            # Comunicaciones RF
            (
                link_results,
                distances_km,
            ) = self.calculate_links()

            # Estados del supervisor
            cognitive_states = []

            for satellite_id in self.satellite_ids:
                energy_system = (
                    self.energy_systems[
                        satellite_id
                    ]
                )

                link = link_results[
                    satellite_id
                ]

                cognitive_states.append(
                    SatelliteCognitiveState(
                        satellite_id=(
                            satellite_id
                        ),
                        soc=energy_system.soc,
                        energy_mode=(
                            energy_system.mode
                        ),
                        temperature_c=(
                            self.temperatures_c[
                                satellite_id
                            ]
                        ),
                        formation_error_m=(
                            formation_errors[
                                satellite_id
                            ]
                        ),
                        link_margin_db=(
                            link.link_margin_db
                        ),
                        link_available=(
                            link.link_available
                        ),
                        training_requested=(
                            federated_round_due
                        ),
                    )
                )

            fleet_decision = (
                self.cognitive_supervisor
                .evaluate_fleet(
                    cognitive_states
                )
            )

            decisions = {
                decision.satellite_id: decision
                for decision
                in fleet_decision
                .satellite_decisions
            }

            # Cambios de acción cognitiva
            for (
                satellite_id,
                decision,
            ) in decisions.items():
                current_action = (
                    decision.action.value
                )

                previous_action = (
                    previous_actions.get(
                        satellite_id
                    )
                )

                if (
                    current_action
                    != previous_action
                ):
                    events.append(
                        {
                            "time_s": time_s,
                            "time_min": (
                                time_s / 60.0
                            ),
                            "category": (
                                "SUPERVISOR"
                            ),
                            "message": (
                                f"{satellite_id}: "
                                f"{current_action}. "
                                f"{decision.reason}"
                            ),
                        }
                    )

                    previous_actions[
                        satellite_id
                    ] = current_action

            # =================================================
            # RONDA FEDERADA
            # =================================================

            federated_round_executed = False

            selected_clients: tuple[
                str,
                ...,
            ] = tuple()

            if federated_round_due:
                if (
                    fleet_decision
                    .federated_round_allowed
                ):
                    round_result = (
                        self
                        .federated_coordinator
                        .run_round(
                            eligible_client_ids=list(
                                fleet_decision
                                .eligible_federated_clients
                            ),
                            local_epochs=3,
                            learning_rate=0.20,
                        )
                    )

                    federated_round_executed = (
                        True
                    )

                    selected_clients = (
                        round_result
                        .selected_clients
                    )

                    federated_rounds.append(
                        {
                            "time_s": time_s,
                            "time_min": (
                                time_s / 60.0
                            ),
                            "round_number": (
                                round_result
                                .round_number
                            ),
                            "selected_clients": (
                                list(
                                    round_result
                                    .selected_clients
                                )
                            ),
                            "excluded_clients": (
                                list(
                                    round_result
                                    .excluded_clients
                                )
                            ),
                            "global_loss": (
                                round_result
                                .global_loss
                            ),
                            "global_accuracy": (
                                round_result
                                .global_accuracy
                            ),
                        }
                    )

                    events.append(
                        {
                            "time_s": time_s,
                            "time_min": (
                                time_s / 60.0
                            ),
                            "category": "FEDAVG",
                            "message": (
                                "Ronda federada "
                                f"{round_result.round_number} "
                                "completada"
                            ),
                        }
                    )

                else:
                    cancelled_rounds += 1

                    events.append(
                        {
                            "time_s": time_s,
                            "time_min": (
                                time_s / 60.0
                            ),
                            "category": "FEDAVG",
                            "message": (
                                "Ronda federada "
                                "cancelada por falta "
                                "de participantes"
                            ),
                        }
                    )

            # =================================================
            # REGISTRAR SNAPSHOTS
            # =================================================

            for satellite_id in self.satellite_ids:
                state = self.relative_states[
                    satellite_id
                ]

                link = link_results[
                    satellite_id
                ]

                decision = decisions[
                    satellite_id
                ]

                snapshots.append(
                    {
                        "time_s": time_s,
                        "time_min": (
                            time_s / 60.0
                        ),
                        "illuminated": (
                            illuminated
                        ),
                        "satellite_id": (
                            satellite_id
                        ),
                        "position_m": (
                            self.vector_to_list(
                                state[0:3]
                            )
                        ),
                        "velocity_m_s": (
                            self.vector_to_list(
                                state[3:6]
                            )
                        ),
                        "formation_error_m": (
                            formation_errors[
                                satellite_id
                            ]
                        ),
                        "control_acceleration_m_s2": (
                            self.vector_to_list(
                                control_commands[
                                    satellite_id
                                ]
                            )
                        ),
                        "distance_to_leader_km": (
                            distances_km[
                                satellite_id
                            ]
                        ),
                        "link_margin_db": (
                            link.link_margin_db
                        ),
                        "ebn0_db": (
                            link.ebn0_db
                        ),
                        "link_available": (
                            link.link_available
                        ),
                        "soc": (
                            self.energy_systems[
                                satellite_id
                            ].soc
                        ),
                        "energy_mode": (
                            self.energy_systems[
                                satellite_id
                            ].mode.value
                        ),
                        "temperature_c": (
                            self.temperatures_c[
                                satellite_id
                            ]
                        ),
                        "cognitive_action": (
                            decision.action.value
                        ),
                        "federated_eligible": (
                            decision
                            .federated_training_allowed
                        ),
                    }
                )

            # No avanzar después del último registro
            if (
                step_index
                == self.number_of_steps
            ):
                break

            # =================================================
            # ACTUALIZAR ENERGÍA Y TEMPERATURA
            # =================================================

            for satellite_id in self.satellite_ids:
                decision = decisions[
                    satellite_id
                ]

                training_active = (
                    federated_round_executed
                    and satellite_id
                    in selected_clients
                )

                loads = EnergyLoads(
                    housekeeping_active=True,
                    control_active=(
                        decision.control_active
                    ),
                    isl_active=(
                        decision
                        .isl_control_channel_active
                    ),
                    federated_training_active=(
                        training_active
                    ),
                )

                self.energy_systems[
                    satellite_id
                ].step(
                    time_step_s=(
                        self.time_step_s
                    ),
                    illuminated=illuminated,
                    loads=loads,
                )

                base_temperature = (
                    24.0
                    if illuminated
                    else 18.0
                )

                target_temperature = (
                    base_temperature
                    + 0.25
                    * loads.total_power_w()
                )

                thermal_alpha = min(
                    self.time_step_s / 600.0,
                    1.0,
                )

                current_temperature = (
                    self.temperatures_c[
                        satellite_id
                    ]
                )

                self.temperatures_c[
                    satellite_id
                ] = (
                    current_temperature
                    + thermal_alpha
                    * (
                        target_temperature
                        - current_temperature
                    )
                )

            # =================================================
            # ACTUALIZAR FORMACIÓN HCW
            # =================================================

            for satellite_id in self.satellite_ids:
                if satellite_id == self.leader_id:
                    continue

                self.relative_states[
                    satellite_id
                ] = rk4_step(
                    state=(
                        self.relative_states[
                            satellite_id
                        ]
                    ),
                    control_acceleration_m_s2=(
                        control_commands[
                            satellite_id
                        ]
                    ),
                    time_step_s=(
                        self.time_step_s
                    ),
                    orbital_mean_motion_rad_s=(
                        self.orbital_mean_motion
                    ),
                )

        # =====================================================
        # RESUMEN FINAL
        # =====================================================

        final_metrics = (
            self.federated_coordinator
            .evaluate_global_model()
        )

        def satellite_snapshots(
            satellite_id: str,
        ) -> list[dict[str, Any]]:
            return [
                snapshot
                for snapshot in snapshots
                if snapshot["satellite_id"]
                == satellite_id
            ]

        initial_errors = {
            satellite_id: (
                satellite_snapshots(
                    satellite_id
                )[0]["formation_error_m"]
            )
            for satellite_id
            in self.satellite_ids
        }

        final_errors = {
            satellite_id: (
                satellite_snapshots(
                    satellite_id
                )[-1]["formation_error_m"]
            )
            for satellite_id
            in self.satellite_ids
        }

        summary = {
            "duration_s": self.duration_s,
            "time_step_s": self.time_step_s,
            "satellite_count": len(
                self.satellite_ids
            ),
            "initial_formation_errors_m": (
                initial_errors
            ),
            "final_formation_errors_m": (
                final_errors
            ),
            "minimum_soc": min(
                snapshot["soc"]
                for snapshot in snapshots
            ),
            "minimum_link_margin_db": min(
                snapshot["link_margin_db"]
                for snapshot in snapshots
            ),
            "initial_global_loss": (
                self.initial_federated_metrics
                .loss
            ),
            "final_global_loss": (
                final_metrics.loss
            ),
            "initial_global_accuracy": (
                self.initial_federated_metrics
                .accuracy
            ),
            "final_global_accuracy": (
                final_metrics.accuracy
            ),
            "federated_rounds_completed": (
                len(federated_rounds)
            ),
            "federated_rounds_cancelled": (
                cancelled_rounds
            ),
            "event_count": len(events),
        }

        return {
            "snapshots": snapshots,
            "events": events,
            "federated_rounds": (
                federated_rounds
            ),
            "summary": summary,
        }


def save_integrated_result(
    result: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Guarda el resultado integrado en JSON."""

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path