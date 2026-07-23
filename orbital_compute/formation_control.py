"""
Dinámica relativa y control distribuido de formación del Grupo 3.

El módulo implementa:

1. Movimiento medio para una órbita circular.
2. Ecuaciones linealizadas de Clohessy-Wiltshire-Hill.
3. Control proporcional-derivativo líder-seguidor.
4. Saturación de la aceleración de control.
5. Integración numérica Runge-Kutta de cuarto orden.
6. Simulación independiente de un satélite seguidor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from orbital_compute import config_g3


def _as_vector3(value: object, name: str) -> np.ndarray:
    """Convierte un valor en un vector NumPy tridimensional."""

    vector = np.asarray(value, dtype=float)

    if vector.shape != (3,):
        raise ValueError(f"{name} debe tener exactamente tres componentes")

    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} contiene valores no finitos")

    return vector


def _as_state6(value: object, name: str = "state") -> np.ndarray:
    """Convierte un valor en un estado [x, y, z, vx, vy, vz]."""

    state = np.asarray(value, dtype=float)

    if state.shape != (6,):
        raise ValueError(
            f"{name} debe contener [x, y, z, vx, vy, vz]"
        )

    if not np.all(np.isfinite(state)):
        raise ValueError(f"{name} contiene valores no finitos")

    return state


def mean_motion_rad_s(
    altitude_km: float = config_g3.ORBIT_ALTITUDE_KM,
    earth_radius_km: float = config_g3.EARTH_RADIUS_KM,
    gravitational_parameter_km3_s2: float = (
        config_g3.EARTH_GRAVITATIONAL_PARAMETER_KM3_S2
    ),
) -> float:
    """
    Calcula el movimiento medio de una órbita circular.

    n = sqrt(mu / a^3)

    Parameters
    ----------
    altitude_km:
        Altitud orbital sobre la superficie terrestre, en km.
    earth_radius_km:
        Radio terrestre de referencia, en km.
    gravitational_parameter_km3_s2:
        Parámetro gravitacional terrestre, en km^3/s^2.

    Returns
    -------
    float
        Movimiento medio orbital en rad/s.
    """

    if altitude_km <= 0.0:
        raise ValueError("La altitud orbital debe ser positiva")

    if earth_radius_km <= 0.0:
        raise ValueError("El radio terrestre debe ser positivo")

    if gravitational_parameter_km3_s2 <= 0.0:
        raise ValueError("El parámetro gravitacional debe ser positivo")

    semi_major_axis_km = earth_radius_km + altitude_km

    return float(
        np.sqrt(
            gravitational_parameter_km3_s2
            / semi_major_axis_km**3
        )
    )


def saturate_vector(
    vector: object,
    maximum_norm: float,
) -> np.ndarray:
    """
    Limita la norma de un vector sin alterar su dirección.

    Parameters
    ----------
    vector:
        Vector tridimensional.
    maximum_norm:
        Norma máxima permitida.

    Returns
    -------
    numpy.ndarray
        Vector original o vector escalado.
    """

    result = _as_vector3(vector, "vector")

    if maximum_norm <= 0.0:
        raise ValueError("maximum_norm debe ser positivo")

    norm = float(np.linalg.norm(result))

    if norm <= maximum_norm or norm == 0.0:
        return result.copy()

    return result * (maximum_norm / norm)


@dataclass(frozen=True)
class FormationController:
    """
    Controlador PD para un satélite seguidor.

    La aceleración comandada se calcula mediante:

        u = -Kp * error_posicion - Kd * error_velocidad
    """

    kp: float = config_g3.FORMATION_KP
    kd: float = config_g3.FORMATION_KD
    maximum_acceleration_m_s2: float = (
        config_g3.MAX_CONTROL_ACCELERATION_M_S2
    )

    def __post_init__(self) -> None:
        if self.kp <= 0.0:
            raise ValueError("kp debe ser positivo")

        if self.kd <= 0.0:
            raise ValueError("kd debe ser positivo")

        if self.maximum_acceleration_m_s2 <= 0.0:
            raise ValueError(
                "La aceleración máxima debe ser positiva"
            )

    def command(
        self,
        position_m: object,
        velocity_m_s: object,
        desired_position_m: object,
        desired_velocity_m_s: object = (0.0, 0.0, 0.0),
    ) -> np.ndarray:
        """
        Calcula la aceleración de control del seguidor.

        Returns
        -------
        numpy.ndarray
            Aceleración comandada [ux, uy, uz] en m/s^2.
        """

        position = _as_vector3(position_m, "position_m")
        velocity = _as_vector3(velocity_m_s, "velocity_m_s")

        desired_position = _as_vector3(
            desired_position_m,
            "desired_position_m",
        )

        desired_velocity = _as_vector3(
            desired_velocity_m_s,
            "desired_velocity_m_s",
        )

        position_error = position - desired_position
        velocity_error = velocity - desired_velocity

        unconstrained_acceleration = (
            -self.kp * position_error
            -self.kd * velocity_error
        )

        return saturate_vector(
            unconstrained_acceleration,
            self.maximum_acceleration_m_s2,
        )


def hcw_derivative(
    state: object,
    control_acceleration_m_s2: object,
    orbital_mean_motion_rad_s: float,
) -> np.ndarray:
    """
    Evalúa las ecuaciones de Clohessy-Wiltshire-Hill.

    State:
        [x, y, z, vx, vy, vz]

    Returns:
        [vx, vy, vz, ax, ay, az]
    """

    relative_state = _as_state6(state)
    control = _as_vector3(
        control_acceleration_m_s2,
        "control_acceleration_m_s2",
    )

    if orbital_mean_motion_rad_s <= 0.0:
        raise ValueError(
            "El movimiento medio orbital debe ser positivo"
        )

    x, y, z, vx, vy, vz = relative_state
    ux, uy, uz = control
    n = orbital_mean_motion_rad_s

    ax = 3.0 * n**2 * x + 2.0 * n * vy + ux
    ay = -2.0 * n * vx + uy
    az = -n**2 * z + uz

    return np.array(
        [vx, vy, vz, ax, ay, az],
        dtype=float,
    )


def rk4_step(
    state: object,
    control_acceleration_m_s2: object,
    time_step_s: float,
    orbital_mean_motion_rad_s: float,
) -> np.ndarray:
    """
    Integra las ecuaciones HCW usando Runge-Kutta de cuarto orden.

    La aceleración de control se mantiene constante durante el paso.
    """

    current_state = _as_state6(state)
    control = _as_vector3(
        control_acceleration_m_s2,
        "control_acceleration_m_s2",
    )

    if time_step_s <= 0.0:
        raise ValueError("El paso temporal debe ser positivo")

    derivative = lambda current: hcw_derivative(
        current,
        control,
        orbital_mean_motion_rad_s,
    )

    k1 = derivative(current_state)
    k2 = derivative(current_state + 0.5 * time_step_s * k1)
    k3 = derivative(current_state + 0.5 * time_step_s * k2)
    k4 = derivative(current_state + time_step_s * k3)

    return current_state + (
        time_step_s / 6.0
    ) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def simulate_follower(
    initial_state: object,
    desired_position_m: object,
    duration_s: float,
    time_step_s: float = config_g3.TIME_STEP_S,
    controller: FormationController | None = None,
) -> dict[str, np.ndarray]:
    """
    Simula un satélite seguidor respecto al líder.

    Parameters
    ----------
    initial_state:
        Estado inicial [x, y, z, vx, vy, vz].
    desired_position_m:
        Posición relativa deseada.
    duration_s:
        Duración de la simulación.
    time_step_s:
        Paso de integración.
    controller:
        Controlador. Si se omite, se utiliza FormationController.

    Returns
    -------
    dict
        Historial de tiempo, estados, aceleraciones y errores.
    """

    if duration_s <= 0.0:
        raise ValueError("La duración debe ser positiva")

    if time_step_s <= 0.0:
        raise ValueError("El paso temporal debe ser positivo")

    state = _as_state6(initial_state).copy()
    desired_position = _as_vector3(
        desired_position_m,
        "desired_position_m",
    )

    active_controller = controller or FormationController()
    orbital_mean_motion = mean_motion_rad_s()

    number_of_steps = int(np.floor(duration_s / time_step_s)) + 1

    times = np.zeros(number_of_steps, dtype=float)
    states = np.zeros((number_of_steps, 6), dtype=float)
    controls = np.zeros((number_of_steps, 3), dtype=float)
    errors = np.zeros(number_of_steps, dtype=float)

    for index in range(number_of_steps):
        current_time = index * time_step_s
        position = state[0:3]
        velocity = state[3:6]

        control = active_controller.command(
            position_m=position,
            velocity_m_s=velocity,
            desired_position_m=desired_position,
        )

        times[index] = current_time
        states[index] = state
        controls[index] = control
        errors[index] = np.linalg.norm(
            position - desired_position
        )

        if index < number_of_steps - 1:
            state = rk4_step(
                state=state,
                control_acceleration_m_s2=control,
                time_step_s=time_step_s,
                orbital_mean_motion_rad_s=orbital_mean_motion,
            )

    return {
        "time_s": times,
        "state": states,
        "control_m_s2": controls,
        "position_error_m": errors,
    }