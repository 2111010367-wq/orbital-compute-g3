"""
Pruebas del simulador integrado del proyecto G3.

Se valida la integración de:

- Control de formación HCW.
- Sistema energético.
- Enlace inter-satélite en banda Ka.
- Supervisor cognitivo.
- Aprendizaje federado FedAvg.
- Exportación de resultados.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from orbital_compute import config_g3
from orbital_compute.integrated_simulator_g3 import (
    IntegratedG3Simulator,
    save_integrated_result,
)


class TestIntegratedG3Simulator(unittest.TestCase):
    """Valida el comportamiento del simulador integrado."""

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ejecuta una única simulación para todas las pruebas.

        Duración:
            30 minutos.

        Paso temporal:
            60 segundos.

        Intervalo FedAvg:
            10 minutos.
        """

        cls.duration_s = 1800.0
        cls.time_step_s = 60.0
        cls.federated_interval_s = 600.0

        cls.simulator = IntegratedG3Simulator(
            duration_s=cls.duration_s,
            time_step_s=cls.time_step_s,
            federated_interval_s=(
                cls.federated_interval_s
            ),
            random_seed=42,
        )

        cls.result = cls.simulator.run()

        cls.snapshots = cls.result["snapshots"]
        cls.events = cls.result["events"]
        cls.federated_rounds = cls.result[
            "federated_rounds"
        ]
        cls.summary = cls.result["summary"]

    @classmethod
    def snapshots_for(
        cls,
        satellite_id: str,
    ) -> list[dict]:
        """Obtiene los registros de un satélite."""

        return [
            snapshot
            for snapshot in cls.snapshots
            if snapshot["satellite_id"]
            == satellite_id
        ]

    def test_invalid_time_configuration_is_rejected(
        self,
    ) -> None:
        """La duración debe ser múltiplo del paso."""

        with self.assertRaises(ValueError):
            IntegratedG3Simulator(
                duration_s=650.0,
                time_step_s=60.0,
                federated_interval_s=300.0,
            )

    def test_result_contains_required_sections(
        self,
    ) -> None:
        """El resultado debe contener todas las secciones."""

        self.assertIn(
            "snapshots",
            self.result,
        )
        self.assertIn(
            "events",
            self.result,
        )
        self.assertIn(
            "federated_rounds",
            self.result,
        )
        self.assertIn(
            "summary",
            self.result,
        )

    def test_snapshot_count_is_correct(
        self,
    ) -> None:
        """Debe existir un registro por satélite y paso."""

        number_of_time_instants = (
            int(
                self.duration_s
                / self.time_step_s
            )
            + 1
        )

        expected_snapshot_count = (
            number_of_time_instants
            * config_g3.NUM_SATELLITES
        )

        self.assertEqual(
            len(self.snapshots),
            expected_snapshot_count,
        )

    def test_all_satellites_are_present(
        self,
    ) -> None:
        """Los tres satélites deben aparecer."""

        satellite_ids = {
            snapshot["satellite_id"]
            for snapshot in self.snapshots
        }

        self.assertEqual(
            satellite_ids,
            set(config_g3.SATELLITE_IDS),
        )

    def test_formation_controller_reduces_error(
        self,
    ) -> None:
        """
        Cada seguidor debe alcanzar un error menor
        que su error inicial durante la simulación.
        """

        follower_ids = [
            config_g3.FOLLOWER_1_ID,
            config_g3.FOLLOWER_2_ID,
        ]

        for satellite_id in follower_ids:
            satellite_history = (
                self.snapshots_for(
                    satellite_id
                )
            )

            errors = [
                snapshot["formation_error_m"]
                for snapshot in satellite_history
            ]

            initial_error = errors[0]
            minimum_error = min(errors)

            self.assertGreater(
                initial_error,
                0.0,
            )

            self.assertLess(
                minimum_error,
                initial_error,
            )

    def test_soc_remains_in_valid_interval(
        self,
    ) -> None:
        """El SOC siempre debe permanecer entre 0 y 1."""

        for snapshot in self.snapshots:
            self.assertGreaterEqual(
                snapshot["soc"],
                0.0,
            )

            self.assertLessEqual(
                snapshot["soc"],
                1.0,
            )

    def test_rf_results_are_finite(
        self,
    ) -> None:
        """Las métricas RF deben ser numéricamente válidas."""

        for snapshot in self.snapshots:
            self.assertTrue(
                np.isfinite(
                    snapshot["link_margin_db"]
                )
            )

            self.assertTrue(
                np.isfinite(
                    snapshot["ebn0_db"]
                )
            )

            self.assertIsInstance(
                snapshot["link_available"],
                bool,
            )

    def test_federated_attempts_match_schedule(
        self,
    ) -> None:
        """
        Las rondas completadas y canceladas deben
        coincidir con los instantes programados.
        """

        expected_attempts = (
            int(
                self.duration_s
                / self.federated_interval_s
            )
            + 1
        )

        actual_attempts = (
            self.summary[
                "federated_rounds_completed"
            ]
            + self.summary[
                "federated_rounds_cancelled"
            ]
        )

        self.assertEqual(
            actual_attempts,
            expected_attempts,
        )

    def test_result_can_be_saved_as_json(
        self,
    ) -> None:
        """El resultado debe poder exportarse y recuperarse."""

        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "simulacion_integrada.json"
            )

            saved_path = save_integrated_result(
                result=self.result,
                output_path=output_path,
            )

            self.assertTrue(
                saved_path.exists()
            )

            recovered_result = json.loads(
                saved_path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertIn(
                "summary",
                recovered_result,
            )

            self.assertEqual(
                recovered_result["summary"][
                    "satellite_count"
                ],
                3,
            )


if __name__ == "__main__":
    unittest.main()