"""Pruebas de la visualización orbital 3D del dashboard G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.figures.orbit_3d import (
    COLOR_DEGRADED,
    COLOR_FAILURE,
    build_orbit_3d_figure,
)


SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
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


def build_orbit_result(
    satellite_failure: bool = False,
    isl_blackout: bool = False,
) -> dict[str, Any]:
    """Construye snapshots orbitales controlados."""

    snapshots: list[dict[str, Any]] = []

    for time_s in (
        0.0,
        600.0,
    ):
        for index, satellite_id in enumerate(
            SATELLITE_IDS
        ):
            operational = True
            link_available = True

            if (
                satellite_failure
                and satellite_id == "SAT-001"
                and time_s == 600.0
            ):
                operational = False

            if (
                isl_blackout
                and satellite_id == "SAT-002"
                and time_s == 600.0
            ):
                link_available = False

            snapshots.append(
                {
                    "time_s": time_s,
                    "time_min": time_s / 60.0,
                    "satellite_id": satellite_id,
                    "position_m": [
                        index * 500.0,
                        index * 0.10
                        + time_s * 0.0001,
                        index * 0.01,
                    ],
                    "velocity_m_s": [
                        0.0,
                        0.001,
                        0.0,
                    ],
                    "satellite_operational": (
                        operational
                    ),
                    "link_available": (
                        link_available
                    ),
                    "soc": (
                        0.80
                        - index * 0.10
                    ),
                    "link_margin_db": (
                        41.0
                        - index
                    ),
                    "formation_error_m": (
                        index * 0.05
                    ),
                }
            )

    return {
        "snapshots": snapshots,
        "events": [],
        "federated_rounds": [],
        "summary": {},
    }


def build_dashboard_dataset() -> dict[str, Any]:
    """Construye un dataset completo para Dash."""

    nominal_result = build_orbit_result()

    scenarios = {
        scenario: nominal_result
        for scenario in SCENARIOS
    }

    summaries = {
        scenario: {
            "scenario": scenario,
            "satellite_count": 3,
            "satellite_ids": list(
                SATELLITE_IDS
            ),
            "duration_s": 600.0,
            "duration_min": 10.0,
            "snapshot_count": len(
                nominal_result["snapshots"]
            ),
            "event_count": 0,
            "federated_round_count": 0,
        }
        for scenario in SCENARIOS
    }

    assessments = {
        scenario: {
            "scenario": scenario,
            "score": 100.0,
            "classification": "ROBUSTO",
        }
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
        "scenario_summaries": summaries,
        "assessment": assessments,
        "comparison": {
            scenario: {
                "scenario": scenario,
            }
            for scenario in SCENARIOS
        },
    }


class TestDashboardOrbit3DG3(
    unittest.TestCase
):
    """Valida la representación orbital real."""

    def test_orbit_figure_contains_seven_traces(
        self,
    ) -> None:
        """Tres trayectorias, tres ISL y una formación."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(),
            scenario_name="NOMINAL",
        )

        self.assertEqual(
            len(figure.data),
            7,
        )

    def test_orbit_title_contains_scenario(
        self,
    ) -> None:
        """El título debe identificar el escenario."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(),
            scenario_name=(
                "FORMATION_DISTURBANCE"
            ),
        )

        self.assertIn(
            "FORMATION_DISTURBANCE",
            figure.layout.title.text,
        )

    def test_three_trajectories_are_created(
        self,
    ) -> None:
        """Debe existir una trayectoria por satélite."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(),
            scenario_name="NOMINAL",
        )

        trajectories = [
            trace
            for trace in figure.data
            if str(trace.name).startswith(
                "Trayectoria"
            )
        ]

        self.assertEqual(
            len(trajectories),
            3,
        )

    def test_three_isl_links_are_created(
        self,
    ) -> None:
        """Tres nodos deben formar tres enlaces."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(),
            scenario_name="NOMINAL",
        )

        links = [
            trace
            for trace in figure.data
            if str(trace.name).startswith(
                "ISL"
            )
        ]

        self.assertEqual(
            len(links),
            3,
        )

    def test_current_formation_has_three_nodes(
        self,
    ) -> None:
        """La formación actual debe tener tres puntos."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(),
            scenario_name="NOMINAL",
        )

        formation_trace = next(
            trace
            for trace in figure.data
            if trace.name
            == "Formación actual"
        )

        self.assertEqual(
            len(formation_trace.x),
            3,
        )

    def test_failed_satellite_uses_failure_color(
        self,
    ) -> None:
        """Un nodo fallado debe representarse en rojo."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(
                satellite_failure=True
            ),
            scenario_name=(
                "SATELLITE_FAILURE"
            ),
        )

        formation_trace = next(
            trace
            for trace in figure.data
            if trace.name
            == "Formación actual"
        )

        self.assertIn(
            COLOR_FAILURE,
            list(
                formation_trace.marker.color
            ),
        )

    def test_blackout_uses_degraded_link_color(
        self,
    ) -> None:
        """El blackout debe degradar enlaces ISL."""

        figure = build_orbit_3d_figure(
            result=build_orbit_result(
                isl_blackout=True
            ),
            scenario_name="ISL_BLACKOUT",
        )

        link_colors = [
            trace.line.color
            for trace in figure.data
            if str(trace.name).startswith(
                "ISL"
            )
        ]

        self.assertIn(
            COLOR_DEGRADED,
            link_colors,
        )

    def test_dashboard_registers_orbit_output(
        self,
    ) -> None:
        """El selector debe actualizar la órbita 3D."""

        app = create_app(
            dataset=(
                build_dashboard_dataset()
            )
        )

        callback_outputs = " ".join(
            app.callback_map.keys()
        )

        self.assertIn(
            "orbit-3d-graph",
            callback_outputs,
        )


if __name__ == "__main__":
    unittest.main()