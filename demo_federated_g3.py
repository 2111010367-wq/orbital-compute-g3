"""Demostración de aprendizaje federado real del proyecto G3."""

from orbital_compute.federated_real_g3 import (
    FederatedCoordinator,
    make_satellite_datasets,
)


def main() -> None:
    (
        clients,
        evaluation_features,
        evaluation_labels,
    ) = make_satellite_datasets(
        samples_per_client=120,
        evaluation_samples=300,
        random_seed=42,
    )

    coordinator = FederatedCoordinator(
        clients=clients,
        evaluation_features=evaluation_features,
        evaluation_labels=evaluation_labels,
    )

    initial_metrics = coordinator.evaluate_global_model()

    print("=" * 94)
    print("APRENDIZAJE FEDERADO REAL — PROYECTO G3")
    print("=" * 94)
    print(
        f"Modelo inicial | "
        f"Pérdida={initial_metrics.loss:.4f} | "
        f"Precisión={100.0 * initial_metrics.accuracy:.2f}%"
    )
    print("-" * 94)

    all_satellites = [
        "SAT-000",
        "SAT-001",
        "SAT-002",
    ]

    for round_number in range(1, 11):
        # Durante las rondas 5, 6 y 7 se simula que SAT-002
        # queda excluido por restricción energética.
        if 5 <= round_number <= 7:
            eligible_satellites = [
                "SAT-000",
                "SAT-001",
            ]

            exclusion_reason = (
                "SAT-002 excluido por SOC bajo"
            )
        else:
            eligible_satellites = all_satellites
            exclusion_reason = "Sin exclusiones"

        result = coordinator.run_round(
            eligible_client_ids=eligible_satellites,
            local_epochs=3,
            learning_rate=0.20,
        )

        participants = ", ".join(
            result.selected_clients
        )

        print(
            f"Ronda {result.round_number:2d} | "
            f"Participan: {participants:27} | "
            f"Pérdida={result.global_loss:.4f} | "
            f"Precisión={100.0 * result.global_accuracy:6.2f}%"
        )

        print(
            f"          Decisión: {exclusion_reason}"
        )

    final_metrics = coordinator.evaluate_global_model()

    print("-" * 94)
    print(
        f"Modelo final   | "
        f"Pérdida={final_metrics.loss:.4f} | "
        f"Precisión={100.0 * final_metrics.accuracy:.2f}%"
    )


if __name__ == "__main__":
    main()