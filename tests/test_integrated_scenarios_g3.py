"""Pruebas de integración de escenarios con el simulador G3."""

from __future__ import annotations

import unittest

from orbital_compute import config_g3
from orbital_compute.integrated_simulator_g3 import IntegratedG3Simulator
from orbital_compute.scenarios_g3 import ScenarioName


class TestIntegratedScenariosG3(unittest.TestCase):
    """Valida que las fallas afecten al simulador integrado."""

    @staticmethod
    def run_scenario(scenario: ScenarioName) -> dict:
        simulator = IntegratedG3Simulator(
            duration_s=3600.0,
            time_step_s=60.0,
            federated_interval_s=600.0,
            random_seed=42,
            scenario=scenario,
        )
        return simulator.run()

    @staticmethod
    def snapshots_for(result: dict, satellite_id: str) -> list[dict]:
        return [
            snapshot
            for snapshot in result["snapshots"]
            if snapshot["satellite_id"] == satellite_id
        ]

    def test_nominal_is_default_and_preserves_baseline(self) -> None:
        result = IntegratedG3Simulator(
            duration_s=1800.0,
            time_step_s=60.0,
            federated_interval_s=600.0,
            random_seed=42,
        ).run()

        self.assertEqual(result["summary"]["scenario"], "NOMINAL")
        self.assertEqual(result["summary"]["scenario_event_count"], 0)
        self.assertEqual(result["summary"]["disabled_satellite_snapshot_count"], 0)

    def test_low_power_reduces_satellite_soc(self) -> None:
        result = self.run_scenario(ScenarioName.LOW_POWER)
        history = self.snapshots_for(result, config_g3.FOLLOWER_2_ID)
        at_injection = next(item for item in history if item["time_s"] == 900.0)

        self.assertAlmostEqual(at_injection["soc"], 0.18)
        self.assertIn("SET_SOC", [
            event["effect"]
            for event in result["events"]
            if event.get("category") == "ESCENARIO"
        ])

    def test_isl_degradation_reduces_margin_temporarily(self) -> None:
        result = self.run_scenario(ScenarioName.ISL_DEGRADATION)
        history = self.snapshots_for(result, config_g3.FOLLOWER_1_ID)
        before = next(item for item in history if item["time_s"] == 840.0)
        during = next(item for item in history if item["time_s"] == 900.0)
        after = next(item for item in history if item["time_s"] == 1800.0)

        self.assertLess(during["link_margin_db"], before["link_margin_db"] - 30.0)
        self.assertGreater(after["link_margin_db"], during["link_margin_db"] + 30.0)
        self.assertIn("ADD_LINK_LOSS_DB", during["scenario_effects"])

    def test_isl_blackout_forces_link_unavailable(self) -> None:
        result = self.run_scenario(ScenarioName.ISL_BLACKOUT)
        history = self.snapshots_for(result, config_g3.FOLLOWER_2_ID)
        before = next(item for item in history if item["time_s"] == 1140.0)
        during = next(item for item in history if item["time_s"] == 1200.0)
        after = next(item for item in history if item["time_s"] == 1800.0)

        self.assertTrue(before["link_available"])
        self.assertFalse(during["link_available"])
        self.assertTrue(after["link_available"])
        self.assertIn("FORCE_LINK_DOWN", during["scenario_effects"])

    def test_satellite_failure_disables_node_and_control(self) -> None:
        result = self.run_scenario(ScenarioName.SATELLITE_FAILURE)
        history = self.snapshots_for(result, config_g3.FOLLOWER_2_ID)
        failed = next(item for item in history if item["time_s"] == 1800.0)

        self.assertFalse(failed["satellite_operational"])
        self.assertFalse(failed["link_available"])
        self.assertEqual(failed["control_acceleration_m_s2"], [0.0, 0.0, 0.0])
        self.assertGreater(result["summary"]["disabled_satellite_snapshot_count"], 0)

    def test_formation_disturbance_creates_error_jump(self) -> None:
        result = self.run_scenario(ScenarioName.FORMATION_DISTURBANCE)
        history = self.snapshots_for(result, config_g3.FOLLOWER_1_ID)
        before = next(item for item in history if item["time_s"] == 1140.0)
        disturbed = next(item for item in history if item["time_s"] == 1200.0)

        self.assertGreater(
            disturbed["formation_error_m"],
            before["formation_error_m"] + 100.0,
        )

    def test_federated_exclusion_removes_client_during_window(self) -> None:
        result = self.run_scenario(ScenarioName.FEDERATED_EXCLUSION)
        history = self.snapshots_for(result, config_g3.FOLLOWER_1_ID)

        for time_s in (600.0, 1200.0, 1800.0):
            snapshot = next(
                item for item in history
                if item["time_s"] == time_s
            )
            self.assertTrue(snapshot["scenario_federated_excluded"])
            self.assertFalse(snapshot["federated_eligible"])

        recovered = next(
            item for item in history
            if item["time_s"] == 2400.0
        )
        self.assertFalse(recovered["scenario_federated_excluded"])

        for round_result in result["federated_rounds"]:
            if round_result["time_s"] in (1200.0, 1800.0):
                self.assertNotIn(
                    config_g3.FOLLOWER_1_ID,
                    round_result["selected_clients"],
                )

    def test_combined_failure_records_all_three_effects(self) -> None:
        result = self.run_scenario(ScenarioName.COMBINED_FAILURE)
        effects = {
            event["effect"]
            for event in result["events"]
            if event.get("category") == "ESCENARIO"
            and event.get("transition") == "INICIO"
        }

        self.assertEqual(
            effects,
            {"ADD_POSITION_OFFSET", "ADD_LINK_LOSS_DB", "SET_SOC"},
        )
        self.assertEqual(result["summary"]["scenario"], "COMBINED_FAILURE")


if __name__ == "__main__":
    unittest.main()
