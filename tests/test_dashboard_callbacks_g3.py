"""Pruebas de los callbacks dinámicos del dashboard G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.callbacks import (
    build_scenario_view,
    build_telemetry_cards,
)
from dashboard_g3.data_loader import (
    SCENARIO_ORDER,
)


def component_text(
    component: Any,
) -> str:
    """Extrae recursivamente el texto visible."""

    if component is None:
        return ""

    if isinstance(
        component,
        (str, int, float),
    ):
        return str(component)

    if isinstance(
        component,
        (list, tuple),
    ):
        return " ".join(
            component_text(child)
            for child in component
        )

    children = getattr(
        component,
        "children",
        None,
    )

    return component_text(
        children
    )


def build_test_dataset() -> dict:
    """Construye resultados controlados para pruebas."""

    scenarios: dict[str, dict] = {}
    summaries: dict[str, dict] = {}
    assessments: dict[str, dict] = {}
    comparison: dict[str, dict] = {}

    for scenario in SCENARIO_ORDER:
        final_soc = {
            "SAT-000": 0.80,
            "SAT-001": 0.65,
            "SAT-002": 0.45,
        }

        if scenario == "LOW_POWER":
            final_soc["SAT-002"] = 0.12

        snapshots = []

        for satellite_index, satellite_id in enumerate(
            (
                "SAT-000",
                "SAT-001",
                "SAT-002",
            )
        ):
            snapshots.append(
                {
                    "time_s": 0.0,
                    "satellite_id": satellite_id,
                    "soc": 0.75,
                    "link_margin_db": 40.0,
                    "formation_error_m": (
                        satellite_index * 25.0
                    ),
                    "link_available": True,
                    "satellite_enabled": True,
                }
            )

            final_snapshot = {
                "time_s": 3600.0,
                "satellite_id": satellite_id,
                "soc": final_soc[
                    satellite_id
                ],
                "link_margin_db": 35.0,
                "formation_error_m": (
                    satellite_index * 0.03
                ),
                "link_available": True,
                "satellite_enabled": True,
            }

            if (
                scenario
                == "SATELLITE_FAILURE"
                and satellite_id == "SAT-001"
            ):
                final_snapshot[
                    "satellite_enabled"
                ] = False

            if (
                scenario
                == "ISL_BLACKOUT"
                and satellite_id == "SAT-002"
            ):
                final_snapshot[
                    "link_available"
                ] = False

            snapshots.append(
                final_snapshot
            )

        events = [
            {
                "time_s": 1200.0,
                "event_type": "SUPERVISOR",
                "description": (
                    f"Decisión para {scenario}."
                ),
            }
        ]

        scenarios[scenario] = {
            "snapshots": snapshots,
            "events": events,
            "federated_rounds": [],
            "summary": {},
        }

        summaries[scenario] = {
            "scenario": scenario,
            "snapshot_count": len(
                snapshots
            ),
            "event_count": len(events),
            "federated_round_count": 7,
            "satellite_count": 3,
            "satellite_ids": [
                "SAT-000",
                "SAT-001",
                "SAT-002",
            ],
            "duration_s": 3600.0,
            "duration_min": 60.0,
        }

        score = 100.0

        if scenario == "LOW_POWER":
            score = 93.9
        elif scenario == "SATELLITE_FAILURE":
            score = 69.7

        assessments[scenario] = {
            "scenario": scenario,
            "score": score,
            "classification": (
                "CRITICO"
                if scenario
                == "SATELLITE_FAILURE"
                else "ROBUSTO"
            ),
        }

        comparison[scenario] = {
            "scenario": scenario,
        }

    return {
        "scenario_order": list(
            SCENARIO_ORDER
        ),
        "scenario_count": 8,
        "scenarios": scenarios,
        "scenario_summaries": summaries,
        "assessment": assessments,
        "comparison": comparison,
    }


class TestDashboardCallbacksG3(
    unittest.TestCase
):
    """Valida la actualización del selector."""

    def setUp(self) -> None:
        """Prepara el dataset."""

        self.dataset = (
            build_test_dataset()
        )

    def test_nominal_view_has_required_values(
        self,
    ) -> None:
        """La vista nominal debe estar completa."""

        view = build_scenario_view(
            self.dataset,
            "NOMINAL",
        )

        self.assertEqual(
            view["satellite_count"],
            "3",
        )

        self.assertEqual(
            view["duration"],
            "60.0",
        )

        self.assertEqual(
            view["resilience_score"],
            "100.0",
        )

    def test_low_power_displays_reduced_soc(
        self,
    ) -> None:
        """LOW_POWER debe mostrar el SOC reducido."""

        view = build_scenario_view(
            self.dataset,
            "LOW_POWER",
        )

        telemetry_text = component_text(
            view["telemetry"]
        )

        self.assertIn(
            "12.0 %",
            telemetry_text,
        )

        self.assertIn(
            "DEGRADADO",
            telemetry_text,
        )

    def test_satellite_failure_displays_offline(
        self,
    ) -> None:
        """La falla debe indicar fuera de servicio."""

        view = build_scenario_view(
            self.dataset,
            "SATELLITE_FAILURE",
        )

        telemetry_text = component_text(
            view["telemetry"]
        )

        self.assertIn(
            "FUERA DE SERVICIO",
            telemetry_text,
        )

    def test_blackout_displays_degraded_state(
        self,
    ) -> None:
        """Un blackout debe degradar la telemetría."""

        view = build_scenario_view(
            self.dataset,
            "ISL_BLACKOUT",
        )

        telemetry_text = component_text(
            view["telemetry"]
        )

        self.assertIn(
            "DEGRADADO",
            telemetry_text,
        )

    def test_three_telemetry_cards_are_created(
        self,
    ) -> None:
        """Deben construirse tres tarjetas."""

        summary = self.dataset[
            "scenario_summaries"
        ]["NOMINAL"]

        snapshots = self.dataset[
            "scenarios"
        ]["NOMINAL"]["snapshots"]

        cards = build_telemetry_cards(
            summary=summary,
            snapshots=snapshots,
        )

        self.assertEqual(
            len(cards),
            3,
        )

    def test_event_feed_is_generated(
        self,
    ) -> None:
        """El registro de eventos debe actualizarse."""

        view = build_scenario_view(
            self.dataset,
            "NOMINAL",
        )

        self.assertGreater(
            len(view["event_feed"]),
            0,
        )

        self.assertIn(
            "SUPERVISOR",
            component_text(
                view["event_feed"]
            ),
        )

    def test_unknown_scenario_is_rejected(
        self,
    ) -> None:
        """Un escenario inexistente debe rechazarse."""

        with self.assertRaises(KeyError):
            build_scenario_view(
                self.dataset,
                "UNKNOWN_SCENARIO",
            )

    def test_callback_is_registered_in_app(
        self,
    ) -> None:
        """La aplicación debe registrar el callback."""

        app = create_app(
            dataset=self.dataset
        )

        self.assertGreaterEqual(
            len(app.callback_map),
            1,
        )

        callback_outputs = " ".join(
            app.callback_map.keys()
        )

        self.assertIn(
            "kpi-resilience-score",
            callback_outputs,
        )

        self.assertIn(
            "telemetry-panel",
            callback_outputs,
        )


if __name__ == "__main__":
    unittest.main()