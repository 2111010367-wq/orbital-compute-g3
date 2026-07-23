"""Pruebas del supervisor cognitivo del proyecto G3."""

import unittest

from orbital_compute.cognitive_supervisor_g3 import (
    CognitiveAction,
    CognitiveSupervisor,
    SatelliteCognitiveState,
)
from orbital_compute.energy_g3 import OperatingMode


def make_state(
    satellite_id: str = "SAT-000",
    soc: float = 0.80,
    energy_mode: OperatingMode = OperatingMode.NORMAL,
    temperature_c: float = 25.0,
    formation_error_m: float = 5.0,
    link_margin_db: float = 20.0,
    link_available: bool = True,
    training_requested: bool = True,
) -> SatelliteCognitiveState:
    """Construye un estado nominal modificable."""

    return SatelliteCognitiveState(
        satellite_id=satellite_id,
        soc=soc,
        energy_mode=energy_mode,
        temperature_c=temperature_c,
        formation_error_m=formation_error_m,
        link_margin_db=link_margin_db,
        link_available=link_available,
        training_requested=training_requested,
    )


class TestCognitiveSupervisorG3(unittest.TestCase):
    """Valida prioridades y selección federada."""

    def setUp(self) -> None:
        self.supervisor = CognitiveSupervisor()

    def test_nominal_satellite_participates(self) -> None:
        decision = self.supervisor.decide(make_state())

        self.assertEqual(
            decision.action,
            CognitiveAction.NOMINAL,
        )
        self.assertTrue(
            decision.federated_training_allowed
        )

    def test_low_soc_blocks_federated_training(self) -> None:
        decision = self.supervisor.decide(
            make_state(
                soc=0.25,
                energy_mode=OperatingMode.POWER_SAVE,
            )
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.POWER_SAVE,
        )
        self.assertFalse(
            decision.federated_training_allowed
        )

    def test_critical_soc_has_high_priority(self) -> None:
        decision = self.supervisor.decide(
            make_state(
                soc=0.10,
                energy_mode=OperatingMode.CRITICAL,
                formation_error_m=200.0,
            )
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.CRITICAL_POWER,
        )

    def test_large_formation_error_is_prioritized(self) -> None:
        decision = self.supervisor.decide(
            make_state(formation_error_m=100.0)
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.RECOVER_FORMATION,
        )
        self.assertTrue(decision.control_active)
        self.assertFalse(
            decision.federated_training_allowed
        )

    def test_bad_link_blocks_federated_training(self) -> None:
        decision = self.supervisor.decide(
            make_state(
                link_margin_db=-3.0,
                link_available=False,
            )
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.LINK_DEGRADED,
        )
        self.assertFalse(
            decision.isl_control_channel_active
        )

    def test_high_temperature_activates_protection(self) -> None:
        decision = self.supervisor.decide(
            make_state(temperature_c=52.0)
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.THERMAL_PROTECTION,
        )

    def test_critical_temperature_has_top_priority(self) -> None:
        decision = self.supervisor.decide(
            make_state(
                soc=0.10,
                temperature_c=65.0,
                formation_error_m=300.0,
            )
        )

        self.assertEqual(
            decision.action,
            CognitiveAction.THERMAL_CRITICAL,
        )
        self.assertEqual(decision.priority, 1)

    def test_fleet_round_allowed_with_two_clients(self) -> None:
        result = self.supervisor.evaluate_fleet(
            [
                make_state("SAT-000"),
                make_state("SAT-001"),
                make_state(
                    "SAT-002",
                    soc=0.25,
                    energy_mode=OperatingMode.POWER_SAVE,
                ),
            ]
        )

        self.assertTrue(result.federated_round_allowed)
        self.assertEqual(
            result.eligible_federated_clients,
            ("SAT-000", "SAT-001"),
        )

    def test_fleet_round_cancelled_with_one_client(self) -> None:
        result = self.supervisor.evaluate_fleet(
            [
                make_state("SAT-000"),
                make_state(
                    "SAT-001",
                    formation_error_m=100.0,
                ),
                make_state(
                    "SAT-002",
                    soc=0.25,
                    energy_mode=OperatingMode.POWER_SAVE,
                ),
            ]
        )

        self.assertFalse(result.federated_round_allowed)
        self.assertEqual(
            result.eligible_federated_clients,
            ("SAT-000",),
        )


if __name__ == "__main__":
    unittest.main()