"""Demostración energética de tres CubeSats del proyecto G3."""

from orbital_compute.energy_g3 import (
    CubeSatEnergySystem,
    EnergyLoads,
)


def main() -> None:
    satellites = {
        "SAT-000": CubeSatEnergySystem(initial_soc=0.80),
        "SAT-001": CubeSatEnergySystem(initial_soc=0.65),
        "SAT-002": CubeSatEnergySystem(initial_soc=0.40),
    }

    time_step_s = 300.0
    duration_s = 5400.0

    print("=" * 92)
    print("GESTIÓN ENERGÉTICA DE TRES CUBESATS — PROYECTO G3")
    print("=" * 92)

    for time_s in range(
        0,
        int(duration_s) + 1,
        int(time_step_s),
    ):
        # Escenario académico simplificado:
        # 60 minutos iluminado y 30 minutos en eclipse.
        illuminated = time_s < 3600.0

        print(
            f"\nTiempo: {time_s / 60.0:5.1f} min | "
            f"Iluminación: {'SOL' if illuminated else 'ECLIPSE'}"
        )

        for satellite_id, energy_system in satellites.items():
            training_requested = satellite_id != "SAT-002"

            training_active = (
                training_requested
                and energy_system.federated_training_allowed()
            )

            result = energy_system.step(
                time_step_s=time_step_s,
                illuminated=illuminated,
                loads=EnergyLoads(
                    control_active=True,
                    isl_active=True,
                    federated_training_active=training_active,
                ),
            )

            print(
                f"{satellite_id} | "
                f"SOC={100.0 * result.soc:6.2f}% | "
                f"Pload={result.load_power_w:5.1f} W | "
                f"Pnet={result.net_power_w:6.1f} W | "
                f"Modo={result.mode.value:15} | "
                f"FL={'SÍ' if result.federated_training_allowed else 'NO'}"
            )


if __name__ == "__main__":
    main()