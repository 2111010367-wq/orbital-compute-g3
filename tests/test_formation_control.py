"""Pruebas de dinámica y control de formación del Grupo 3."""

import unittest

import numpy as np

from orbital_compute.formation_control import (
    FormationController,
    hcw_derivative,
    mean_motion_rad_s,
    rk4_step,
    saturate_vector,
    simulate_follower,
)


class TestFormationControl(unittest.TestCase):
    """Valida las ecuaciones HCW y el controlador PD."""

    def test_mean_motion_at_550_km(self) -> None:
        mean_motion = mean_motion_rad_s(altitude_km=550.0)

        self.assertGreater(mean_motion, 1.0e-3)
        self.assertLess(mean_motion, 1.2e-3)

    def test_zero_error_produces_zero_control(self) -> None:
        controller = FormationController()

        control = controller.command(
            position_m=(0.0, 1000.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
            desired_position_m=(0.0, 1000.0, 0.0),
        )

        np.testing.assert_allclose(
            control,
            np.zeros(3),
            atol=1.0e-15,
        )

    def test_controller_corrects_positive_y_error(self) -> None:
        controller = FormationController()

        control = controller.command(
            position_m=(0.0, 1200.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
            desired_position_m=(0.0, 1000.0, 0.0),
        )

        self.assertLess(control[1], 0.0)

    def test_control_acceleration_is_saturated(self) -> None:
        maximum_acceleration = 1.0e-3

        saturated = saturate_vector(
            vector=(2.0, 0.0, 0.0),
            maximum_norm=maximum_acceleration,
        )

        self.assertAlmostEqual(
            np.linalg.norm(saturated),
            maximum_acceleration,
            places=12,
        )

    def test_along_track_equilibrium(self) -> None:
        mean_motion = mean_motion_rad_s()

        derivative = hcw_derivative(
            state=(0.0, 1000.0, 0.0, 0.0, 0.0, 0.0),
            control_acceleration_m_s2=(0.0, 0.0, 0.0),
            orbital_mean_motion_rad_s=mean_motion,
        )

        np.testing.assert_allclose(
            derivative,
            np.zeros(6),
            atol=1.0e-15,
        )

    def test_rk4_result_is_finite(self) -> None:
        next_state = rk4_step(
            state=(10.0, 1000.0, 5.0, 0.0, 0.0, 0.0),
            control_acceleration_m_s2=(0.0, 0.0, 0.0),
            time_step_s=1.0,
            orbital_mean_motion_rad_s=mean_motion_rad_s(),
        )

        self.assertEqual(next_state.shape, (6,))
        self.assertTrue(np.all(np.isfinite(next_state)))

    def test_controller_reduces_formation_error(self) -> None:
        result = simulate_follower(
            initial_state=(
                0.0,
                1200.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            desired_position_m=(0.0, 1000.0, 0.0),
            duration_s=1200.0,
            time_step_s=1.0,
        )

        initial_error = result["position_error_m"][0]
        final_error = result["position_error_m"][-1]

        self.assertLess(final_error, initial_error)
        self.assertLess(final_error, 0.40 * initial_error)


if __name__ == "__main__":
    unittest.main()