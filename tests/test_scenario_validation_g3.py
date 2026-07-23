"""Pruebas de ejecución y exportación de escenarios G3."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from demo_scenarios_g3 import (
    run_all_scenarios,
)
from orbital_compute.scenarios_g3 import (
    ScenarioName,
)


class TestScenarioValidationG3(
    unittest.TestCase
):
    """Valida la campaña de escenarios."""

    @classmethod
    def setUpClass(cls) -> None:
        """Ejecuta una campaña para todas las pruebas."""

        cls.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        cls.output_directory = Path(
            cls.temporary_directory.name
        )

        cls.generated_files = (
            run_all_scenarios(
                output_directory=(
                    cls.output_directory
                ),
                verbose=False,
            )
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """Elimina los archivos temporales."""

        cls.temporary_directory.cleanup()

    def test_eight_json_files_are_generated(
        self,
    ) -> None:
        """Deben generarse ocho resultados."""

        self.assertEqual(
            len(self.generated_files),
            len(ScenarioName),
        )

        self.assertEqual(
            set(self.generated_files),
            {
                scenario.value
                for scenario in ScenarioName
            },
        )

    def test_all_generated_files_exist(
        self,
    ) -> None:
        """Todos los JSON deben existir."""

        for path in (
            self.generated_files.values()
        ):
            self.assertTrue(
                path.exists()
            )

            self.assertGreater(
                path.stat().st_size,
                0,
            )

    def test_each_json_has_required_sections(
        self,
    ) -> None:
        """Cada archivo debe contener el resultado completo."""

        required_sections = {
            "scenario",
            "snapshots",
            "events",
            "federated_rounds",
            "summary",
        }

        for path in (
            self.generated_files.values()
        ):
            result = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertTrue(
                required_sections.issubset(
                    result
                )
            )

            self.assertEqual(
                result["summary"][
                    "satellite_count"
                ],
                3,
            )

            self.assertEqual(
                len(result["snapshots"]),
                183,
            )

    def test_summary_matches_requested_scenario(
        self,
    ) -> None:
        """El escenario del resumen debe coincidir."""

        for (
            scenario_name,
            path,
        ) in self.generated_files.items():
            result = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                result["summary"][
                    "scenario"
                ],
                scenario_name,
            )

            self.assertEqual(
                result["scenario"][
                    "name"
                ],
                scenario_name,
            )

    def test_nominal_and_failure_events_differ(
        self,
    ) -> None:
        """Nominal no inyecta fallas; los demás sí."""

        for scenario in ScenarioName:
            path = self.generated_files[
                scenario.value
            ]

            result = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            scenario_events = [
                event
                for event in result["events"]
                if event.get("category")
                == "ESCENARIO"
            ]

            if (
                scenario
                == ScenarioName.NOMINAL
            ):
                self.assertEqual(
                    scenario_events,
                    [],
                )
            else:
                self.assertGreater(
                    len(scenario_events),
                    0,
                    msg=scenario.value,
                )


if __name__ == "__main__":
    unittest.main()