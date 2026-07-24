"""Pruebas de entrega atómica de las cuatro gráficas temporales."""

from __future__ import annotations

import unittest

from dashboard_g3.app import create_app


def find_component(component, component_id):
    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(component, "children", None)
    if children is None:
        return None

    if not isinstance(children, (list, tuple)):
        children = [children]

    for child in children:
        found = find_component(child, component_id)
        if found is not None:
            return found

    return None


class TestDashboardTemporalAtomicG3(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshots = []
        for satellite_id, error, soc, margin in (
            ("SAT-000", 0.0, 0.80, 40.0),
            ("SAT-001", 200.0, 0.65, 40.0),
            ("SAT-002", 50.0, 0.25, 41.0),
        ):
            snapshots.append(
                {
                    "time_s": 0.0,
                    "satellite_id": satellite_id,
                    "formation_error_m": error,
                    "soc": soc,
                    "link_margin_db": margin,
                    "link_available": True,
                }
            )

        result = {
            "snapshots": snapshots,
            "events": [],
            "federated_rounds": [],
            "summary": {},
        }

        summary = {
            "scenario": "NOMINAL",
            "snapshot_count": 3,
            "event_count": 0,
            "federated_round_count": 0,
            "satellite_count": 3,
            "satellite_ids": ["SAT-000", "SAT-001", "SAT-002"],
            "duration_s": 0.0,
            "duration_min": 0.0,
        }

        cls.dataset = {
            "scenario_order": ["NOMINAL"],
            "scenario_count": 1,
            "scenarios": {"NOMINAL": result},
            "scenario_summaries": {"NOMINAL": summary},
            "assessment": {
                "NOMINAL": {
                    "score": 100.0,
                    "classification": "ROBUSTO",
                }
            },
            "comparison": {"NOMINAL": {}},
        }
        cls.app = create_app(dataset=cls.dataset)

    def test_temporal_store_exists(self) -> None:
        store = find_component(
            self.app.layout,
            "temporal-figures-store",
        )
        self.assertIsNotNone(store)

    def test_server_writes_atomic_store(self) -> None:
        callback_outputs = " ".join(self.app.callback_map.keys())
        self.assertIn(
            "temporal-figures-store.data",
            callback_outputs,
        )

    def test_each_graph_has_one_callback_owner(self) -> None:
        for output_id in (
            "graph-formation-error.figure",
            "graph-soc.figure",
            "graph-link-margin.figure",
            "graph-isl-availability.figure",
        ):
            owners = [
                key
                for key in self.app.callback_map
                if output_id in key
            ]
            self.assertEqual(len(owners), 1)


if __name__ == "__main__":
    unittest.main()
