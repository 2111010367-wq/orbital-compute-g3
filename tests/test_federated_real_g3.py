"""Pruebas del aprendizaje federado real del proyecto G3."""

import unittest

import numpy as np

from orbital_compute.federated_real_g3 import (
    ClientUpdate,
    FederatedCoordinator,
    ModelParameters,
    binary_cross_entropy,
    fedavg,
    make_satellite_datasets,
    sigmoid,
)


class TestFederatedRealG3(unittest.TestCase):
    """Valida entrenamiento local y agregación FedAvg."""

    def setUp(self) -> None:
        (
            self.clients,
            self.evaluation_features,
            self.evaluation_labels,
        ) = make_satellite_datasets(random_seed=42)

    def test_sigmoid_at_zero(self) -> None:
        result = sigmoid(np.array([0.0]))

        self.assertAlmostEqual(
            float(result[0]),
            0.5,
            places=12,
        )

    def test_binary_cross_entropy_is_positive(self) -> None:
        loss = binary_cross_entropy(
            labels=np.array([0.0, 1.0]),
            probabilities=np.array([0.25, 0.75]),
        )

        self.assertGreater(loss, 0.0)

    def test_local_training_reduces_loss(self) -> None:
        client = self.clients["SAT-000"]

        initial_model = ModelParameters(
            weights=np.zeros(2),
            bias=0.0,
        )

        update = client.local_train(
            global_model=initial_model,
            epochs=5,
            learning_rate=0.20,
        )

        self.assertLess(
            update.loss_after,
            update.loss_before,
        )

    def test_fedavg_is_weighted_by_samples(self) -> None:
        update_1 = ClientUpdate(
            client_id="SAT-A",
            sample_count=1,
            model=ModelParameters(
                weights=np.array([0.0, 0.0]),
                bias=0.0,
            ),
            loss_before=1.0,
            loss_after=0.5,
            accuracy_after=0.8,
        )

        update_2 = ClientUpdate(
            client_id="SAT-B",
            sample_count=3,
            model=ModelParameters(
                weights=np.array([4.0, 8.0]),
                bias=4.0,
            ),
            loss_before=1.0,
            loss_after=0.4,
            accuracy_after=0.9,
        )

        result = fedavg([update_1, update_2])

        np.testing.assert_allclose(
            result.weights,
            np.array([3.0, 6.0]),
        )

        self.assertAlmostEqual(
            result.bias,
            3.0,
        )

    def test_round_excludes_ineligible_client(self) -> None:
        coordinator = FederatedCoordinator(
            clients=self.clients,
            evaluation_features=self.evaluation_features,
            evaluation_labels=self.evaluation_labels,
        )

        result = coordinator.run_round(
            eligible_client_ids=[
                "SAT-000",
                "SAT-001",
            ],
            local_epochs=2,
        )

        self.assertEqual(
            result.selected_clients,
            ("SAT-000", "SAT-001"),
        )

        self.assertIn(
            "SAT-002",
            result.excluded_clients,
        )

    def test_insufficient_participants_is_rejected(self) -> None:
        coordinator = FederatedCoordinator(
            clients=self.clients,
            evaluation_features=self.evaluation_features,
            evaluation_labels=self.evaluation_labels,
        )

        with self.assertRaises(ValueError):
            coordinator.run_round(
                eligible_client_ids=["SAT-000"],
            )

    def test_global_loss_decreases(self) -> None:
        coordinator = FederatedCoordinator(
            clients=self.clients,
            evaluation_features=self.evaluation_features,
            evaluation_labels=self.evaluation_labels,
        )

        initial_loss = (
            coordinator.evaluate_global_model().loss
        )

        for _ in range(5):
            coordinator.run_round(
                eligible_client_ids=[
                    "SAT-000",
                    "SAT-001",
                    "SAT-002",
                ],
                local_epochs=3,
                learning_rate=0.20,
            )

        final_loss = (
            coordinator.evaluate_global_model().loss
        )

        self.assertLess(final_loss, initial_loss)

    def test_global_accuracy_improves(self) -> None:
        coordinator = FederatedCoordinator(
            clients=self.clients,
            evaluation_features=self.evaluation_features,
            evaluation_labels=self.evaluation_labels,
        )

        initial_accuracy = (
            coordinator.evaluate_global_model().accuracy
        )

        for _ in range(3):
            coordinator.run_round(
                eligible_client_ids=[
                    "SAT-000",
                    "SAT-001",
                    "SAT-002",
                ],
                local_epochs=3,
                learning_rate=0.20,
            )

        final_accuracy = (
            coordinator.evaluate_global_model().accuracy
        )

        self.assertGreater(
            final_accuracy,
            initial_accuracy,
        )

    def test_generated_data_is_non_iid(self) -> None:
        positive_fractions = [
            float(np.mean(client.labels))
            for client in self.clients.values()
        ]

        self.assertGreater(
            max(positive_fractions)
            - min(positive_fractions),
            0.30,
        )


if __name__ == "__main__":
    unittest.main()