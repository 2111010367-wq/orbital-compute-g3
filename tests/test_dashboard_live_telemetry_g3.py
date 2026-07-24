"""Pruebas de telemetría sincronizada con el reloj G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.animation import (
    slice_result_until_time,
)
from dashboard_g3.app import create_app
from dashboard_g3.callbacks import (
    build_live_telemetry_view,
)


SCENARIOS = (
    "NOMINAL",
    "LOW_POWER",
    "ISL_DEGRADATION",
    "ISL_BLACKOUT",
    "SATELLITE_FAILURE",
    "FORMATION_DISTURBANCE",
    "FEDERATED_EXCLUSION",
    "COMBINED_FAILURE",
)

SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)


def build_result() -> dict[str, Any]:
    """Construye tres instantes con tres satélites."""

    snapshots: list[dict[str, Any]] = []

    for time_s in (
        0.0,
        60.0,
        120.0,
    ):
        for index, satellite_id in enumerate(
            SATELLITE_IDS
        ):
            snapshots.append(
                {
                    "time_s": time_s,
                    "time_min": (
                        time_s / 60.0
                    ),
                    "satellite_id": (
                        satellite_id
                    ),
                    "position_m": [
                        index * 500.0,
                        time_s * 0.001,
                        0.0,
                    ],
                    "velocity_m_s": [
                        0.0,
                        0.001,
                        0.0,
                    ],
                    "formation_error_m": (
                        index * 0.05
                        + time_s / 10000.0
                    ),
                    "soc": (
                        0.90
                        - index * 0.10
                        - time_s / 10000.0
                    ),
                    "link_margin_db": (
                        42.0
                        - time_s / 100.0
                    ),
                    "link_available": True,
                    "satellite_operational": True,
                    "temperature_c": (
                        20.0 + index
                    ),
                }
            )

    return {
        "snapshots": snapshots,
        "events": [],
        "federated_rounds": [],
        "summary": {},
    }


def build_dataset() -> dict[str, Any]:
    """Construye el dataset completo de prueba."""

    result = build_result()

    scenarios = {
        scenario: result
        for scenario in SCENARIOS
    }

    return {
        "scenario_order": list(
            SCENARIOS
        ),
        "scenario_count": len(
            SCENARIOS
        ),
        "scenarios": scenarios,
        "scenario_summaries": {
            scenario: {
                "scenario": scenario,
                "satellite_count": 3,
                "satellite_ids": list(
                    SATELLITE_IDS
                ),
                "duration_s": 120.0,
                "duration_min": 2.0,
                "snapshot_count": len(
                    result["snapshots"]
                ),
                "event_count": 0,
                "federated_round_count": 0,
            }
            for scenario in SCENARIOS
        },
        "assessment": {
            scenario: {
                "scenario": scenario,
                "score": 100.0,
                "classification": "ROBUSTO",
            }
            for scenario in SCENARIOS
        },
        "comparison": {
            scenario: {
                "scenario": scenario,
            }
            for scenario in SCENARIOS
        },
    }


class TestDashboardLiveTelemetryG3(
    unittest.TestCase
):
    """Valida la telemetría sincronizada."""

    def setUp(self) -> None:
        """Prepara datos para cada prueba."""

        self.result = build_result()
        self.dataset = build_dataset()

    def test_zero_time_contains_three_snapshots(
        self,
    ) -> None:
        """En t=0 deben existir tres snapshots."""

        sliced = slice_result_until_time(
            result=self.result,
            target_time_s=0.0,
        )

        self.assertEqual(
            len(sliced["snapshots"]),
            3,
        )

    def test_sixty_seconds_contains_six_snapshots(
        self,
    ) -> None:
        """En t=60 deben conservarse dos instantes."""

        sliced = slice_result_until_time(
            result=self.result,
            target_time_s=60.0,
        )

        self.assertEqual(
            len(sliced["snapshots"]),
            6,
        )

    def test_final_time_contains_all_snapshots(
        self,
    ) -> None:
        """El instante final debe conservar todo."""

        sliced = slice_result_until_time(
            result=self.result,
            target_time_s=120.0,
        )

        self.assertEqual(
            len(sliced["snapshots"]),
            9,
        )

    def test_original_result_is_not_modified(
        self,
    ) -> None:
        """El recorte no debe modificar el original."""

        slice_result_until_time(
            result=self.result,
            target_time_s=0.0,
        )

        self.assertEqual(
            len(self.result["snapshots"]),
            9,
        )

    def test_live_telemetry_is_generated(
        self,
    ) -> None:
        """Debe generarse telemetría de los tres nodos."""

        telemetry = build_live_telemetry_view(
            dataset=self.dataset,
            scenario_name="NOMINAL",
            target_time_s=60.0,
        )

        self.assertIsNotNone(
            telemetry
        )

        telemetry_text = str(
            telemetry
        )

        self.assertIn(
            "SAT-000",
            telemetry_text,
        )

        self.assertIn(
            "SAT-001",
            telemetry_text,
        )

        self.assertIn(
            "SAT-002",
            telemetry_text,
        )

    def test_telemetry_has_single_callback_owner(
        self,
    ) -> None:
        """Solo un callback debe controlar telemetría."""

        app = create_app(
            dataset=self.dataset
        )

        matching_outputs = [
            callback_key
            for callback_key
            in app.callback_map
            if (
                "telemetry-panel.children"
                in callback_key
            )
        ]

        self.assertEqual(
            len(matching_outputs),
            1,
        )


if __name__ == "__main__":
    unittest.main()