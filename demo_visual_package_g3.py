"""Cierre y validación del paquete visual de la Fase 16."""

from __future__ import annotations

from pathlib import Path

from orbital_compute.visual_package_g3 import (
    export_visual_package,
    validate_visual_package,
)


VISUAL_ROOT = (
    Path("resultados")
    / "graficas_fase16"
)

OUTPUT_DIRECTORY = (
    Path("resultados")
    / "paquete_visual_fase16"
)


def main() -> None:
    """Valida y exporta el paquete visual."""

    print("=" * 92)
    print(
        "FASE 16.5 - VALIDACIÓN Y "
        "EMPAQUETADO VISUAL G3"
    )
    print("=" * 92)

    report = validate_visual_package(
        VISUAL_ROOT
    )

    for section, count in (
        report.section_counts.items()
    ):
        print(
            f"{section:<24}: "
            f"{count:>3} archivos"
        )

    print("-" * 92)

    print(
        f"Total de archivos : "
        f"{report.total_files}"
    )

    print(
        f"Tamaño total      : "
        f"{report.total_size_bytes} bytes"
    )

    print(
        f"PNG               : "
        f"{report.format_counts['png']}"
    )

    print(
        f"SVG               : "
        f"{report.format_counts['svg']}"
    )

    print(
        f"PDF               : "
        f"{report.format_counts['pdf']}"
    )

    if not report.valid:
        print("\nERRORES DETECTADOS:")

        for issue in report.issues:
            print(
                f"  - {issue}"
            )

        raise SystemExit(
            "El paquete visual no es válido."
        )

    files = export_visual_package(
        root_directory=VISUAL_ROOT,
        output_directory=OUTPUT_DIRECTORY,
    )

    print("\nPAQUETE VALIDADO CORRECTAMENTE")

    print(
        f"Manifiesto JSON : "
        f"{files['json'].resolve()}"
    )

    print(
        f"Inventario CSV  : "
        f"{files['csv'].resolve()}"
    )

    print("=" * 92)
    print(
        "FASE 16.5 EJECUTADA CORRECTAMENTE"
    )
    print("=" * 92)


if __name__ == "__main__":
    main()