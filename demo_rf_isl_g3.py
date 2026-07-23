"""Demostración del enlace ISL en banda Ka del proyecto G3."""

from orbital_compute.rf_isl_ka import RFISLKa


def main() -> None:
    link = RFISLKa()

    distances_km = [1.0, 10.0, 100.0, 1000.0]

    print("=" * 92)
    print("ENLACE INTER-SATÉLITE RF EN BANDA Ka — PROYECTO G3")
    print("=" * 92)
    print(
        f"{'Distancia':>10} "
        f"{'Lfs':>10} "
        f"{'Pr':>12} "
        f"{'C/N0':>10} "
        f"{'Eb/N0':>10} "
        f"{'Margen':>10} "
        f"{'Estado':>10}"
    )

    for distance_km in distances_km:
        result = link.evaluate(distance_km)

        state = (
            "DISPONIBLE"
            if result.link_available
            else "CAÍDO"
        )

        print(
            f"{distance_km:10.1f} "
            f"{result.free_space_loss_db:10.2f} "
            f"{result.received_power_dbw:12.2f} "
            f"{result.carrier_to_noise_density_dbhz:10.2f} "
            f"{result.ebn0_db:10.2f} "
            f"{result.link_margin_db:10.2f} "
            f"{state:>10}"
        )


if __name__ == "__main__":
    main()