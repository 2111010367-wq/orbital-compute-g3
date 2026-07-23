"""
Exportación de la comparación real de escenarios G3.
"""

from __future__ import annotations

from pathlib import Path

from demo_compare_scenarios_g3 import (
    DEFAULT_RESULTS_DIRECTORY,
    build_comparison_rows,
)
from orbital_compute.comparison_export_g3 import (
    export_comparison_bundle,
)


DEFAULT_OUTPUT_DIRECTORY = (
    Path("resultados")
    / "comparacion_fase15"
)


def print_separator() -> None:
    """Imprime una línea separadora."""

    print("=" * 84)


def main() -> None:
    """Genera los archivos CSV y JSON comparativos."""

    print_separator()
    print(
        "FASE 15.3.3 - EXPORTACIÓN "
        "DE LA COMPARACIÓN DE ESCENARIOS"
    )
    print_separator()

    print(
        "Cargando resultados desde: "
        f"{DEFAULT_RESULTS_DIRECTORY.resolve()}"
    )

    rows = build_comparison_rows(
        DEFAULT_RESULTS_DIRECTORY
    )

    generated_files = (
        export_comparison_bundle(
            rows=rows,
            output_directory=(
                DEFAULT_OUTPUT_DIRECTORY
            ),
        )
    )

    print(
        f"\nEscenarios exportados: "
        f"{len(rows)}"
    )

    print(
        "Archivo CSV: "
        f"{generated_files['csv'].resolve()}"
    )

    print(
        "Archivo JSON: "
        f"{generated_files['json'].resolve()}"
    )

    print_separator()
    print(
        "FASE 15.3.3 EJECUTADA "
        "CORRECTAMENTE"
    )
    print_separator()


if __name__ == "__main__":
    main()