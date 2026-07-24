"""Ejecuta el dashboard profesional del proyecto G3."""

from __future__ import annotations

import os

from dashboard_g3.app import create_app


def main() -> None:
    """Inicia el servidor local."""

    host = os.getenv(
        "G3_DASHBOARD_HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "G3_DASHBOARD_PORT",
            "8050",
        )
    )

    app = create_app()

    print("=" * 88)
    print(
        "FASE 17.1.3 - DASHBOARD "
        "PROFESIONAL G3"
    )
    print("=" * 88)
    print(
        f"Servidor local: "
        f"http://{host}:{port}"
    )
    print(
        "Presiona Ctrl + C para detenerlo."
    )
    print("=" * 88)

    app.run(
    host="127.0.0.1",
    port=8050,
    debug=False,
    use_reloader=False,
    threaded=False,
)


if __name__ == "__main__":
    main()