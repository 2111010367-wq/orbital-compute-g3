"""Pruebas de comparación de escenarios G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from demo_compare_scenarios_g3 import (
    build_comparison_rows,
    load_all_scenario_metrics,
)
from orbital_compute.scenarios_g3 import (
    ScenarioName,
)


def make_result(
    scenario: ScenarioName,
    unavailable_count: int = 0,
    disabled_count: int = 0,
    completed_rounds: int = 5,
    cancelled_rounds: int = 2,
    minimum_soc: float = 0.25,
    minimum_margin_db: float = 40.0,
    maximum_error_m: float = 0.05,
) -> dict:
    """Construye un resultado sintético."""

    return {
        "snapshots": [
            {
                "time_s": float(index)
            }
            for index in range(100)
        ],
        "summary": {
            "scenario": scenario.value,
            "event_count": 10,
            "minimum_soc": minimum_soc,
            "minimum_link_margin_db": (
                minimum_margin_db
            ),
            "link_unavailable_snapshot_count": (
                unavailable_count
            ),
            "disabled_satellite_snapshot_count": (
                disabled_count
            ),
            "federated_rounds_completed": (
                completed_rounds
            ),
            "federated_rounds_cancelled": (
                cancelled_rounds
            ),
            "final_global_accuracy": 0.96,
            "final_formation_errors_m": {
                "SAT-000": 0.0,
                "SAT-001": maximum_error_m,
                "SAT-002": 0.01,
            },
        },
    }


def write_all_results(
    output_directory: Path,
) -> None:
    """Escribe resultados de los ocho escenarios."""

    for scenario in ScenarioName:
        arguments = {}

        if scenario == ScenarioName.LOW_POWER:
            arguments["minimum_soc"] = 0.18

        elif scenario == ScenarioName.ISL_DEGRADATION:
            arguments["minimum_margin_db"] = 6.0

        elif scenario == ScenarioName.ISL_BLACKOUT:
            arguments.update(
                unavailable_count=20,
                completed_rounds=4,
                cancelled_rounds=3,
            )

        elif (
            scenario
            == ScenarioName.SATELLITE_FAILURE
        ):
            arguments.update(
                unavailable_count=50,
                disabled_count=25,
                completed_rounds=1,
                cancelled_rounds=6,
            )

        elif (
            scenario
            == ScenarioName.FORMATION_DISTURBANCE
        ):
            arguments[
                "maximum_error_m"
            ] = 0.70

        elif (
            scenario
            == ScenarioName.COMBINED_FAILURE
        ):
            arguments.update(
                minimum_soc=0.12,
                minimum_margin_db=5.0,
                maximum_error_m=0.14,
            )

        result = make_result(
            scenario=scenario,
            **arguments,
        )

        path = (
            output_directory
            / f"{scenario.value.lower()}.json"
        )

        path.write_text(
            json.dumps(result),
            encoding="utf-8",
        )


class TestCompareScenariosG3(
    unittest.TestCase
):
    """Valida la tabla comparativa."""

    def setUp(self) -> None:
        """Crea una campaña temporal."""

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.output_directory = Path(
            self.temporary_directory.name
        )

        write_all_results(
            self.output_directory
        )

    def tearDown(self) -> None:
        """Elimina la campaña temporal."""

        self.temporary_directory.cleanup()

    def test_all_eight_scenarios_are_loaded(
        self,
    ) -> None:
        """Deben cargarse ocho escenarios."""

        metrics = load_all_scenario_metrics(
            self.output_directory
        )

        self.assertEqual(
            len(metrics),
            8,
        )

        self.assertEqual(
            set(metrics),
            set(ScenarioName),
        )

    def test_comparison_has_eight_rows(
        self,
    ) -> None:
        """La comparación debe tener ocho filas."""

        rows = build_comparison_rows(
            self.output_directory
        )

        self.assertEqual(
            len(rows),
            8,
        )

        self.assertEqual(
            rows[0]["scenario"],
            "NOMINAL",
        )

    def test_nominal_deltas_are_zero(
        self,
    ) -> None:
        """Nominal debe tener diferencias iguales a cero."""

        rows = build_comparison_rows(
            self.output_directory
        )

        nominal = rows[0]

        self.assertAlmostEqual(
            nominal["delta_error_m"],
            0.0,
        )

        self.assertAlmostEqual(
            nominal["delta_soc_pp"],
            0.0,
        )

        self.assertAlmostEqual(
            nominal["delta_margin_db"],
            0.0,
        )

    def test_low_power_detects_soc_degradation(
        self,
    ) -> None:
        """LOW_POWER debe reducir el SOC."""

        rows = build_comparison_rows(
            self.output_directory
        )

        low_power = next(
            row
            for row in rows
            if row["scenario"]
            == "LOW_POWER"
        )

        self.assertLess(
            low_power["delta_soc_pp"],
            0.0,
        )

    def test_blackout_detects_link_degradation(
        self,
    ) -> None:
        """ISL_BLACKOUT debe reducir disponibilidad."""

        rows = build_comparison_rows(
            self.output_directory
        )

        blackout = next(
            row
            for row in rows
            if row["scenario"]
            == "ISL_BLACKOUT"
        )

        self.assertLess(
            blackout[
                "delta_link_availability_pp"
            ],
            0.0,
        )

        self.assertLess(
            blackout[
                "delta_federated_completion_pp"
            ],
            0.0,
        )

    def test_satellite_failure_detects_node_loss(
        self,
    ) -> None:
        """La falla de satélite reduce disponibilidad."""

        rows = build_comparison_rows(
            self.output_directory
        )

        failure = next(
            row
            for row in rows
            if row["scenario"]
            == "SATELLITE_FAILURE"
        )

        self.assertLess(
            failure[
                "delta_node_availability_pp"
            ],
            0.0,
        )

    def test_missing_result_is_rejected(
        self,
    ) -> None:
        """Debe detectarse un JSON faltante."""

        missing_path = (
            self.output_directory
            / "combined_failure.json"
        )

        missing_path.unlink()

        with self.assertRaises(
            FileNotFoundError
        ):
            load_all_scenario_metrics(
                self.output_directory
            )


if __name__ == "__main__":
    unittest.main()