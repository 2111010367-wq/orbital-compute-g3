"""Pruebas del controlador temporal del dashboard G3."""

from __future__ import annotations

import unittest
from typing import Any

from dashboard_g3.animation import (
    advance_animation,
    build_time_axis,
    create_animation_state,
    format_mission_time,
    pause_animation,
    reset_animation,
    start_animation,
)


SATELLITE_IDS = (
    "SAT-000",
    "SAT-001",
    "SAT-002",
)


def build_animation_result() -> dict[str, Any]:
    """Construye una misión con cuatro instantes."""

    snapshots: list[
        dict[str, Any]
    ] = []

    for time_s in (
        0.0,
        60.0,
        120.0,
        180.0,
    ):
        for satellite_index, satellite_id in enumerate(
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
                        (
                            satellite_index
                            * 500.0
                        ),
                        time_s * 0.001,
                        0.0,
                    ],
                    "soc": (
                        0.80
                        - satellite_index
                        * 0.10
                    ),
                }
            )

    return {
        "snapshots": snapshots,
        "events": [],
        "federated_rounds": [],
        "summary": {},
    }


class TestDashboardAnimationG3(
    unittest.TestCase
):
    """Valida el controlador temporal."""

    def setUp(self) -> None:
        """Prepara una misión de prueba."""

        self.result = (
            build_animation_result()
        )

    def test_time_axis_contains_unique_times(
        self,
    ) -> None:
        """Doce snapshots deben producir cuatro tiempos."""

        time_axis = build_time_axis(
            self.result
        )

        self.assertEqual(
            time_axis,
            [
                0.0,
                60.0,
                120.0,
                180.0,
            ],
        )

    def test_initial_state_is_paused(
        self,
    ) -> None:
        """La animación comienza detenida."""

        state = create_animation_state(
            scenario_name="NOMINAL",
            result=self.result,
        )

        self.assertFalse(
            state["running"]
        )

        self.assertEqual(
            state["time_index"],
            0,
        )

        self.assertEqual(
            state["time_s"],
            0.0,
        )

        self.assertEqual(
            state["time_count"],
            4,
        )

    def test_start_enables_animation(
        self,
    ) -> None:
        """Iniciar debe habilitar la reproducción."""

        state = create_animation_state(
            "NOMINAL",
            self.result,
        )

        started = start_animation(
            state=state,
            scenario_name="NOMINAL",
            result=self.result,
        )

        self.assertTrue(
            started["running"]
        )

        self.assertFalse(
            started["completed"]
        )

    def test_advance_uses_unique_time_step(
        self,
    ) -> None:
        """El avance debe saltar de 0 a 60 segundos."""

        state = start_animation(
            state=None,
            scenario_name="NOMINAL",
            result=self.result,
        )

        advanced = advance_animation(
            state=state,
            scenario_name="NOMINAL",
            result=self.result,
        )

        self.assertEqual(
            advanced["time_index"],
            1,
        )

        self.assertEqual(
            advanced["time_s"],
            60.0,
        )

    def test_pause_preserves_current_time(
        self,
    ) -> None:
        """Pausar debe conservar el instante actual."""

        state = start_animation(
            state=None,
            scenario_name="NOMINAL",
            result=self.result,
        )

        state = advance_animation(
            state=state,
            scenario_name="NOMINAL",
            result=self.result,
        )

        paused = pause_animation(
            state=state,
            scenario_name="NOMINAL",
            result=self.result,
        )

        self.assertFalse(
            paused["running"]
        )

        self.assertEqual(
            paused["time_s"],
            60.0,
        )

    def test_reset_returns_to_zero(
        self,
    ) -> None:
        """Reiniciar debe volver al comienzo."""

        state = reset_animation(
            scenario_name="NOMINAL",
            result=self.result,
        )

        self.assertEqual(
            state["time_index"],
            0,
        )

        self.assertEqual(
            state["time_s"],
            0.0,
        )

        self.assertFalse(
            state["running"]
        )

    def test_animation_stops_at_final_time(
        self,
    ) -> None:
        """La misión debe detenerse al finalizar."""

        state = start_animation(
            state=None,
            scenario_name="NOMINAL",
            result=self.result,
        )

        for _ in range(10):
            state = advance_animation(
                state=state,
                scenario_name="NOMINAL",
                result=self.result,
            )

        self.assertEqual(
            state["time_index"],
            3,
        )

        self.assertEqual(
            state["time_s"],
            180.0,
        )

        self.assertTrue(
            state["completed"]
        )

        self.assertFalse(
            state["running"]
        )

        self.assertEqual(
            state["progress_percent"],
            100.0,
        )

    def test_mission_time_format(
        self,
    ) -> None:
        """El reloj debe usar el formato T+HH:MM:SS."""

        self.assertEqual(
            format_mission_time(
                0
            ),
            "T+00:00:00",
        )

        self.assertEqual(
            format_mission_time(
                3661
            ),
            "T+01:01:01",
        )


if __name__ == "__main__":
    unittest.main()