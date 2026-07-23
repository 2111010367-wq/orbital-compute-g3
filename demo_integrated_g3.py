"""Demostración ejecutable del simulador integrado G3."""

from pathlib import Path

from orbital_compute.integrated_simulator_g3 import (
    IntegratedG3Simulator,
    save_integrated_result,
)


def print_separator() -> None:
    """Imprime una línea separadora."""

    print("=" * 78)


def main() -> None:
    """Ejecuta una simulación integrada de una hora."""

    print_separator()
    print("FASE 14.3 - SIMULADOR INTEGRADO G3")
    print_separator()

    duration_s = 3600.0
    time_step_s = 60.0
    federated_interval_s = 600.0
    random_seed = 42

    print("Configuración de la simulación:")
    print(f"Duración            : {duration_s / 60:.0f} minutos")
    print(f"Paso temporal       : {time_step_s:.0f} segundos")
    print(
        "Intervalo FedAvg    : "
        f"{federated_interval_s / 60:.0f} minutos"
    )
    print(f"Semilla aleatoria   : {random_seed}")

    simulator = IntegratedG3Simulator(
        duration_s=duration_s,
        time_step_s=time_step_s,
        federated_interval_s=federated_interval_s,
        random_seed=random_seed,
    )

    print("\nEjecutando simulación integrada...")

    result = simulator.run()
    summary = result["summary"]

    print("\n")
    print_separator()
    print("RESUMEN GENERAL")
    print_separator()

    print(
        f"Número de satélites           : "
        f"{summary['satellite_count']}"
    )
    print(
        f"Duración simulada             : "
        f"{summary['duration_s'] / 60:.0f} min"
    )
    print(
        f"Snapshots registrados         : "
        f"{len(result['snapshots'])}"
    )
    print(
        f"Eventos registrados           : "
        f"{summary['event_count']}"
    )
    print(
        f"Rondas FedAvg completadas     : "
        f"{summary['federated_rounds_completed']}"
    )
    print(
        f"Rondas FedAvg canceladas      : "
        f"{summary['federated_rounds_cancelled']}"
    )

    print("\n")
    print_separator()
    print("CONTROL DE FORMACIÓN")
    print_separator()

    initial_errors = summary[
        "initial_formation_errors_m"
    ]
    final_errors = summary[
        "final_formation_errors_m"
    ]

    for satellite_id in initial_errors:
        initial_error = initial_errors[satellite_id]
        final_error = final_errors[satellite_id]
        reduction = initial_error - final_error

        print(
            f"{satellite_id} | "
            f"inicial = {initial_error:10.3f} m | "
            f"final = {final_error:10.3f} m | "
            f"reducción = {reduction:10.3f} m"
        )

    print("\n")
    print_separator()
    print("ENERGÍA Y COMUNICACIÓN INTER-SATÉLITE")
    print_separator()

    print(
        f"SOC mínimo                     : "
        f"{summary['minimum_soc'] * 100:.2f} %"
    )
    print(
        f"Margen mínimo del enlace Ka    : "
        f"{summary['minimum_link_margin_db']:.2f} dB"
    )

    print("\n")
    print_separator()
    print("APRENDIZAJE FEDERADO")
    print_separator()

    print(
        f"Pérdida global inicial         : "
        f"{summary['initial_global_loss']:.6f}"
    )
    print(
        f"Pérdida global final           : "
        f"{summary['final_global_loss']:.6f}"
    )
    print(
        f"Exactitud global inicial       : "
        f"{summary['initial_global_accuracy'] * 100:.2f} %"
    )
    print(
        f"Exactitud global final         : "
        f"{summary['final_global_accuracy'] * 100:.2f} %"
    )

    output_path = (
        Path("resultados")
        / "simulacion_integrada_g3.json"
    )

    saved_path = save_integrated_result(
        result=result,
        output_path=output_path,
    )

    print("\n")
    print_separator()
    print("EXPORTACIÓN")
    print_separator()

    print(f"Archivo generado: {saved_path.resolve()}")

    print_separator()
    print("FASE 14.3 EJECUTADA CORRECTAMENTE")
    print_separator()


if __name__ == "__main__":
    main()