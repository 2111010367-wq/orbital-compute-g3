"""Pruebas de la interfaz inicial del dashboard G3."""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from dashboard_g3.app import create_app
from dashboard_g3.data_loader import (
    SCENARIO_ORDER,
)
from dashboard_g3.layout import (
    create_dashboard_layout,
)


def find_component(
    component: Any,
    component_id: str,
) -> Any | None:
    """Busca recursivamente un componente Dash."""

    if component is None:
        return None

    if isinstance(
        component,
        (list, tuple),
    ):
        for child in component:
            result = find_component(
                child,
                component_id,
            )

            if result is not None:
                return result

        return None

    if getattr(
        component,
        "id",
        None,
    ) == component_id:
        return component

    children = getattr(
        component,
        "children",
        None,
    )

    return find_component(
        children,
        component_id,
    )


def build_test_dataset() -> dict:
    """Construye un dataset mínimo."""

    scenarios = {}
    summaries = {}
    assessment = {}
    comparison = {}

    for scenario in SCENARIO_ORDER:
        scenarios[scenario] = {
            "snapshots": [],
            "events": [
                {
                    "time_s": 0.0,
                    "event_type": "INFO",
                    "description": (
                        "Evento de validación."
                    ),
                }
            ],
            "federated_rounds": [],
            "summary": {},
        }

        summaries[scenario] = {
            "scenario": scenario,
            "snapshot_count": 183,
            "event_count": 1,
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

        assessment[scenario] = {
            "scenario": scenario,
            "score": 100.0,
            "classification": "ROBUSTO",
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
        "assessment": assessment,
        "comparison": comparison,
    }


class TestDashboardLayoutG3(
    unittest.TestCase
):
    """Valida la interfaz inicial."""

    def setUp(self) -> None:
        """Prepara la interfaz."""

        self.dataset = (
            build_test_dataset()
        )

        self.layout = (
            create_dashboard_layout(
                self.dataset
            )
        )

    def test_required_components_exist(
        self,
    ) -> None:
        """Los componentes principales deben existir."""

        required_ids = (
            "scenario-selector",
            "button-start",
            "button-pause",
            "button-reset",
            "simulation-time",
            "orbit-3d-graph",
            "telemetry-panel",
            "event-feed",
            "kpi-resilience-score",
        )

        for component_id in required_ids:
            self.assertIsNotNone(
                find_component(
                    self.layout,
                    component_id,
                ),
                component_id,
            )

    def test_dropdown_contains_eight_options(
        self,
    ) -> None:
        """El selector debe mostrar ocho escenarios."""

        dropdown = find_component(
            self.layout,
            "scenario-selector",
        )

        self.assertEqual(
            len(dropdown.options),
            8,
        )

    def test_nominal_is_initial_scenario(
        self,
    ) -> None:
        """El escenario inicial debe ser nominal."""

        dropdown = find_component(
            self.layout,
            "scenario-selector",
        )

        self.assertEqual(
            dropdown.value,
            "NOMINAL",
        )

    def test_satellite_kpi_starts_at_three(
        self,
    ) -> None:
        """La formación debe contener tres nodos."""

        kpi = find_component(
            self.layout,
            "kpi-satellite-count",
        )

        self.assertEqual(
            kpi.children,
            "3",
        )

    def test_application_has_expected_title(
        self,
    ) -> None:
        """La aplicación debe tener título propio."""

        app = create_app(
            dataset=self.dataset
        )

        self.assertIn(
            "G3",
            app.title,
        )

        self.assertIsNotNone(
            app.layout
        )

    def test_css_file_exists(
        self,
    ) -> None:
        """La hoja visual debe existir."""

        project_directory = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        css_path = (
            project_directory
            / "dashboard_g3"
            / "assets"
            / "dashboard.css"
        )

        self.assertTrue(
            css_path.exists()
        )

        self.assertGreater(
            css_path.stat().st_size,
            0,
        )


if __name__ == "__main__":
    unittest.main()