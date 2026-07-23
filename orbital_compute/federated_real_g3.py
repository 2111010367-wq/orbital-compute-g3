"""
Aprendizaje federado real para los tres satélites del proyecto G3.

Se implementa:

- Clasificación logística binaria.
- Entrenamiento local en cada satélite.
- Datos locales no IID.
- Agregación FedAvg ponderada por número de muestras.
- Selección de participantes por ronda.
- Evaluación de pérdida y precisión global.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from orbital_compute import config_g3


def sigmoid(values: object) -> np.ndarray:
    """Función sigmoide con protección numérica."""

    array = np.asarray(values, dtype=float)
    clipped = np.clip(array, -60.0, 60.0)

    return 1.0 / (1.0 + np.exp(-clipped))


def binary_cross_entropy(
    labels: object,
    probabilities: object,
) -> float:
    """Calcula la entropía cruzada binaria media."""

    y_true = np.asarray(labels, dtype=float)
    y_probability = np.asarray(probabilities, dtype=float)

    if y_true.shape != y_probability.shape:
        raise ValueError(
            "labels y probabilities deben tener la misma forma"
        )

    epsilon = 1.0e-12

    y_probability = np.clip(
        y_probability,
        epsilon,
        1.0 - epsilon,
    )

    loss = -np.mean(
        y_true * np.log(y_probability)
        + (1.0 - y_true) * np.log(1.0 - y_probability)
    )

    return float(loss)


def classification_accuracy(
    labels: object,
    probabilities: object,
) -> float:
    """Calcula la precisión binaria usando umbral 0.5."""

    y_true = np.asarray(labels, dtype=float)
    y_probability = np.asarray(probabilities, dtype=float)

    if y_true.shape != y_probability.shape:
        raise ValueError(
            "labels y probabilities deben tener la misma forma"
        )

    predictions = (y_probability >= 0.5).astype(float)

    return float(np.mean(predictions == y_true))


@dataclass
class ModelParameters:
    """Parámetros del modelo logístico global o local."""

    weights: np.ndarray
    bias: float

    def copy(self) -> "ModelParameters":
        """Devuelve una copia independiente del modelo."""

        return ModelParameters(
            weights=self.weights.copy(),
            bias=float(self.bias),
        )


@dataclass(frozen=True)
class ModelMetrics:
    """Métricas de evaluación de un modelo."""

    loss: float
    accuracy: float


@dataclass(frozen=True)
class ClientUpdate:
    """Actualización local generada por un satélite."""

    client_id: str
    sample_count: int
    model: ModelParameters

    loss_before: float
    loss_after: float
    accuracy_after: float


@dataclass(frozen=True)
class FederatedRoundResult:
    """Resultado completo de una ronda FedAvg."""

    round_number: int
    selected_clients: tuple[str, ...]
    excluded_clients: tuple[str, ...]

    global_loss: float
    global_accuracy: float

    local_updates: tuple[ClientUpdate, ...]


def evaluate_model(
    model: ModelParameters,
    features: object,
    labels: object,
) -> ModelMetrics:
    """Evalúa pérdida y precisión de un modelo."""

    feature_matrix = np.asarray(features, dtype=float)
    y_true = np.asarray(labels, dtype=float)

    if feature_matrix.ndim != 2:
        raise ValueError("features debe ser una matriz bidimensional")

    if y_true.ndim != 1:
        raise ValueError("labels debe ser un vector")

    if feature_matrix.shape[0] != y_true.shape[0]:
        raise ValueError(
            "El número de muestras y etiquetas debe coincidir"
        )

    if feature_matrix.shape[1] != model.weights.shape[0]:
        raise ValueError(
            "El número de características no coincide con el modelo"
        )

    probabilities = sigmoid(
        feature_matrix @ model.weights + model.bias
    )

    return ModelMetrics(
        loss=binary_cross_entropy(y_true, probabilities),
        accuracy=classification_accuracy(
            y_true,
            probabilities,
        ),
    )


class FederatedClient:
    """Cliente federado que representa un satélite."""

    def __init__(
        self,
        client_id: str,
        features: object,
        labels: object,
    ) -> None:
        self.client_id = str(client_id)
        self.features = np.asarray(features, dtype=float)
        self.labels = np.asarray(labels, dtype=float)

        if not self.client_id:
            raise ValueError("client_id no puede estar vacío")

        if self.features.ndim != 2:
            raise ValueError(
                "features debe ser una matriz bidimensional"
            )

        if self.labels.ndim != 1:
            raise ValueError("labels debe ser un vector")

        if self.features.shape[0] != self.labels.shape[0]:
            raise ValueError(
                "El número de muestras y etiquetas debe coincidir"
            )

        if self.features.shape[0] == 0:
            raise ValueError(
                "El cliente debe contener al menos una muestra"
            )

        if not np.all(np.isfinite(self.features)):
            raise ValueError(
                "features contiene valores no finitos"
            )

        if not np.all(np.isfinite(self.labels)):
            raise ValueError(
                "labels contiene valores no finitos"
            )

        unique_labels = set(np.unique(self.labels).tolist())

        if not unique_labels.issubset({0.0, 1.0}):
            raise ValueError(
                "Las etiquetas solo pueden ser cero o uno"
            )

    @property
    def sample_count(self) -> int:
        """Número de muestras locales."""

        return int(self.features.shape[0])

    @property
    def feature_count(self) -> int:
        """Número de características por muestra."""

        return int(self.features.shape[1])

    def local_train(
        self,
        global_model: ModelParameters,
        epochs: int,
        learning_rate: float,
    ) -> ClientUpdate:
        """
        Entrena localmente mediante descenso de gradiente.

        El modelo global se copia antes del entrenamiento.
        """

        if epochs <= 0:
            raise ValueError("epochs debe ser positivo")

        if learning_rate <= 0.0:
            raise ValueError(
                "learning_rate debe ser positivo"
            )

        local_model = global_model.copy()

        metrics_before = evaluate_model(
            local_model,
            self.features,
            self.labels,
        )

        for _ in range(epochs):
            logits = (
                self.features @ local_model.weights
                + local_model.bias
            )

            probabilities = sigmoid(logits)

            error = probabilities - self.labels

            gradient_weights = (
                self.features.T @ error
            ) / self.sample_count

            gradient_bias = float(np.mean(error))

            local_model.weights -= (
                learning_rate * gradient_weights
            )

            local_model.bias -= (
                learning_rate * gradient_bias
            )

        metrics_after = evaluate_model(
            local_model,
            self.features,
            self.labels,
        )

        return ClientUpdate(
            client_id=self.client_id,
            sample_count=self.sample_count,
            model=local_model,
            loss_before=metrics_before.loss,
            loss_after=metrics_after.loss,
            accuracy_after=metrics_after.accuracy,
        )


def fedavg(
    updates: list[ClientUpdate],
) -> ModelParameters:
    """
    Agrega parámetros usando FedAvg ponderado.

    Cada actualización se pondera por su número de muestras.
    """

    if not updates:
        raise ValueError(
            "Se requiere al menos una actualización"
        )

    reference_shape = updates[0].model.weights.shape

    for update in updates:
        if update.model.weights.shape != reference_shape:
            raise ValueError(
                "Todos los modelos deben tener la misma dimensión"
            )

        if update.sample_count <= 0:
            raise ValueError(
                "sample_count debe ser positivo"
            )

    total_samples = sum(
        update.sample_count
        for update in updates
    )

    aggregated_weights = np.zeros(
        reference_shape,
        dtype=float,
    )

    aggregated_bias = 0.0

    for update in updates:
        client_weight = (
            update.sample_count / total_samples
        )

        aggregated_weights += (
            client_weight * update.model.weights
        )

        aggregated_bias += (
            client_weight * update.model.bias
        )

    return ModelParameters(
        weights=aggregated_weights,
        bias=float(aggregated_bias),
    )


class FederatedCoordinator:
    """Coordinador de las rondas de aprendizaje federado."""

    def __init__(
        self,
        clients: dict[str, FederatedClient],
        evaluation_features: object,
        evaluation_labels: object,
        minimum_participants: int = (
            config_g3.MIN_FEDERATED_PARTICIPANTS
        ),
    ) -> None:
        if not clients:
            raise ValueError(
                "Debe existir al menos un cliente"
            )

        self.clients = dict(clients)

        feature_counts = {
            client.feature_count
            for client in self.clients.values()
        }

        if len(feature_counts) != 1:
            raise ValueError(
                "Todos los clientes deben usar igual número "
                "de características"
            )

        self.feature_count = feature_counts.pop()

        self.evaluation_features = np.asarray(
            evaluation_features,
            dtype=float,
        )

        self.evaluation_labels = np.asarray(
            evaluation_labels,
            dtype=float,
        )

        if minimum_participants <= 0:
            raise ValueError(
                "minimum_participants debe ser positivo"
            )

        self.minimum_participants = minimum_participants

        self.global_model = ModelParameters(
            weights=np.zeros(
                self.feature_count,
                dtype=float,
            ),
            bias=0.0,
        )

        self.round_number = 0

    def evaluate_global_model(self) -> ModelMetrics:
        """Evalúa el modelo global actual."""

        return evaluate_model(
            self.global_model,
            self.evaluation_features,
            self.evaluation_labels,
        )

    def run_round(
        self,
        eligible_client_ids: list[str],
        local_epochs: int = config_g3.LOCAL_EPOCHS,
        learning_rate: float = 0.20,
    ) -> FederatedRoundResult:
        """Ejecuta una ronda completa de FedAvg."""

        selected_ids: list[str] = []

        for client_id in eligible_client_ids:
            if (
                client_id in self.clients
                and client_id not in selected_ids
            ):
                selected_ids.append(client_id)

        if len(selected_ids) < self.minimum_participants:
            raise ValueError(
                "No existen suficientes participantes elegibles"
            )

        updates = [
            self.clients[client_id].local_train(
                global_model=self.global_model,
                epochs=local_epochs,
                learning_rate=learning_rate,
            )
            for client_id in selected_ids
        ]

        self.global_model = fedavg(updates)
        self.round_number += 1

        global_metrics = self.evaluate_global_model()

        excluded_clients = tuple(
            client_id
            for client_id in self.clients
            if client_id not in selected_ids
        )

        return FederatedRoundResult(
            round_number=self.round_number,
            selected_clients=tuple(selected_ids),
            excluded_clients=excluded_clients,
            global_loss=global_metrics.loss,
            global_accuracy=global_metrics.accuracy,
            local_updates=tuple(updates),
        )


def make_satellite_datasets(
    samples_per_client: int = 120,
    evaluation_samples: int = 300,
    random_seed: int = 42,
) -> tuple[
    dict[str, FederatedClient],
    np.ndarray,
    np.ndarray,
]:
    """
    Genera datos sintéticos no IID para tres satélites.

    Los datos representan una tarea binaria sencilla de detección
    o clasificación a partir de dos características.
    """

    if samples_per_client < 20:
        raise ValueError(
            "samples_per_client debe ser al menos 20"
        )

    if evaluation_samples < 20:
        raise ValueError(
            "evaluation_samples debe ser al menos 20"
        )

    generator = np.random.default_rng(random_seed)

    configurations = [
        (
            config_g3.SATELLITE_IDS[0],
            0.70,
            (-1.6, -1.0),
            (1.0, 1.2),
            0.80,
        ),
        (
            config_g3.SATELLITE_IDS[1],
            0.50,
            (-1.1, -1.5),
            (1.5, 0.9),
            0.90,
        ),
        (
            config_g3.SATELLITE_IDS[2],
            0.30,
            (-0.8, -0.9),
            (1.7, 1.5),
            1.00,
        ),
    ]

    clients: dict[str, FederatedClient] = {}

    for (
        client_id,
        class_zero_fraction,
        class_zero_center,
        class_one_center,
        standard_deviation,
    ) in configurations:
        number_class_zero = int(
            samples_per_client * class_zero_fraction
        )

        number_class_one = (
            samples_per_client - number_class_zero
        )

        class_zero_features = generator.normal(
            loc=class_zero_center,
            scale=standard_deviation,
            size=(number_class_zero, 2),
        )

        class_one_features = generator.normal(
            loc=class_one_center,
            scale=standard_deviation,
            size=(number_class_one, 2),
        )

        features = np.vstack(
            [
                class_zero_features,
                class_one_features,
            ]
        )

        labels = np.concatenate(
            [
                np.zeros(number_class_zero),
                np.ones(number_class_one),
            ]
        )

        permutation = generator.permutation(
            samples_per_client
        )

        clients[client_id] = FederatedClient(
            client_id=client_id,
            features=features[permutation],
            labels=labels[permutation],
        )

    number_evaluation_zero = evaluation_samples // 2
    number_evaluation_one = (
        evaluation_samples - number_evaluation_zero
    )

    evaluation_zero = generator.normal(
        loc=(-1.2, -1.2),
        scale=0.90,
        size=(number_evaluation_zero, 2),
    )

    evaluation_one = generator.normal(
        loc=(1.4, 1.3),
        scale=0.90,
        size=(number_evaluation_one, 2),
    )

    evaluation_features = np.vstack(
        [evaluation_zero, evaluation_one]
    )

    evaluation_labels = np.concatenate(
        [
            np.zeros(number_evaluation_zero),
            np.ones(number_evaluation_one),
        ]
    )

    permutation = generator.permutation(
        evaluation_samples
    )

    return (
        clients,
        evaluation_features[permutation],
        evaluation_labels[permutation],
    )