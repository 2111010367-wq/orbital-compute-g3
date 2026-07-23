"""
Balance de enlace inter-satélite RF en banda Ka para el proyecto G3.

El módulo calcula:

- Pérdida de espacio libre.
- PIRE.
- Potencia recibida.
- Densidad espectral de ruido.
- C/N0.
- Eb/N0.
- BER teórica para BPSK/QPSK coherente.
- Margen y disponibilidad del enlace.
- Retardo de propagación.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc, log10, sqrt

from orbital_compute import config_g3


SPEED_OF_LIGHT_M_S = 299_792_458.0
BOLTZMANN_DBW_PER_K_HZ = -228.6


def watts_to_dbw(power_w: float) -> float:
    """Convierte potencia en vatios a dBW."""

    if power_w <= 0.0:
        raise ValueError("La potencia debe ser mayor que cero")

    return 10.0 * log10(power_w)


def free_space_path_loss_db(
    distance_km: float,
    frequency_ghz: float,
) -> float:
    """
    Calcula la pérdida de espacio libre.

    Lfs[dB] = 92.45 + 20log10(f_GHz) + 20log10(d_km)
    """

    if distance_km <= 0.0:
        raise ValueError("La distancia debe ser mayor que cero")

    if frequency_ghz <= 0.0:
        raise ValueError("La frecuencia debe ser mayor que cero")

    return (
        92.45
        + 20.0 * log10(frequency_ghz)
        + 20.0 * log10(distance_km)
    )


def noise_density_dbw_hz(
    system_noise_temperature_k: float,
) -> float:
    """
    Calcula la densidad espectral de ruido térmico.

    N0[dBW/Hz] = -228.6 + 10log10(Ts)
    """

    if system_noise_temperature_k <= 0.0:
        raise ValueError(
            "La temperatura de ruido debe ser mayor que cero"
        )

    return (
        BOLTZMANN_DBW_PER_K_HZ
        + 10.0 * log10(system_noise_temperature_k)
    )


def ber_bpsk_qpsk(ebn0_db: float) -> float:
    """
    BER teórica de BPSK o QPSK coherente sobre canal AWGN.
    """

    ebn0_linear = 10.0 ** (ebn0_db / 10.0)

    return 0.5 * erfc(sqrt(ebn0_linear))


@dataclass(frozen=True)
class RFLinkBudgetResult:
    """Resultados completos del balance del enlace."""

    distance_km: float
    frequency_ghz: float

    transmit_power_dbw: float
    eirp_dbw: float
    free_space_loss_db: float
    received_power_dbw: float

    noise_density_dbw_hz: float
    carrier_to_noise_density_dbhz: float
    ebn0_db: float
    required_ebn0_db: float
    link_margin_db: float

    ber: float
    propagation_delay_s: float
    link_available: bool


@dataclass(frozen=True)
class RFISLKa:
    """Modelo analítico del enlace inter-satélite en banda Ka."""

    frequency_ghz: float = config_g3.ISL_FREQUENCY_GHZ
    bitrate_bps: float = config_g3.ISL_BITRATE_BPS

    transmit_power_w: float = config_g3.TX_POWER_W
    transmit_antenna_gain_dbi: float = (
        config_g3.TX_ANTENNA_GAIN_DBI
    )
    receive_antenna_gain_dbi: float = (
        config_g3.RX_ANTENNA_GAIN_DBI
    )

    transmit_losses_db: float = config_g3.TX_LOSSES_DB
    receive_losses_db: float = config_g3.RX_LOSSES_DB
    pointing_loss_db: float = config_g3.POINTING_LOSS_DB
    polarization_loss_db: float = (
        config_g3.POLARIZATION_LOSS_DB
    )

    system_noise_temperature_k: float = (
        config_g3.SYSTEM_NOISE_TEMPERATURE_K
    )
    required_ebn0_db: float = config_g3.MIN_EBN0_DB

    def __post_init__(self) -> None:
        positive_values = {
            "frequency_ghz": self.frequency_ghz,
            "bitrate_bps": self.bitrate_bps,
            "transmit_power_w": self.transmit_power_w,
            "system_noise_temperature_k": (
                self.system_noise_temperature_k
            ),
        }

        for name, value in positive_values.items():
            if value <= 0.0:
                raise ValueError(f"{name} debe ser positivo")

        losses = {
            "transmit_losses_db": self.transmit_losses_db,
            "receive_losses_db": self.receive_losses_db,
            "pointing_loss_db": self.pointing_loss_db,
            "polarization_loss_db": self.polarization_loss_db,
        }

        for name, value in losses.items():
            if value < 0.0:
                raise ValueError(
                    f"{name} no puede ser negativo"
                )

    def evaluate(
        self,
        distance_km: float,
    ) -> RFLinkBudgetResult:
        """Evalúa el balance completo para una distancia dada."""

        if distance_km <= 0.0:
            raise ValueError("La distancia debe ser positiva")

        transmit_power_dbw = watts_to_dbw(
            self.transmit_power_w
        )

        eirp_dbw = (
            transmit_power_dbw
            + self.transmit_antenna_gain_dbi
            - self.transmit_losses_db
        )

        free_space_loss_db = free_space_path_loss_db(
            distance_km=distance_km,
            frequency_ghz=self.frequency_ghz,
        )

        received_power_dbw = (
            eirp_dbw
            - free_space_loss_db
            - self.pointing_loss_db
            - self.polarization_loss_db
            + self.receive_antenna_gain_dbi
            - self.receive_losses_db
        )

        noise_density = noise_density_dbw_hz(
            self.system_noise_temperature_k
        )

        carrier_to_noise_density = (
            received_power_dbw - noise_density
        )

        ebn0_db = (
            carrier_to_noise_density
            - 10.0 * log10(self.bitrate_bps)
        )

        link_margin_db = (
            ebn0_db - self.required_ebn0_db
        )

        ber = ber_bpsk_qpsk(ebn0_db)

        propagation_delay_s = (
            distance_km * 1000.0
            / SPEED_OF_LIGHT_M_S
        )

        return RFLinkBudgetResult(
            distance_km=distance_km,
            frequency_ghz=self.frequency_ghz,
            transmit_power_dbw=transmit_power_dbw,
            eirp_dbw=eirp_dbw,
            free_space_loss_db=free_space_loss_db,
            received_power_dbw=received_power_dbw,
            noise_density_dbw_hz=noise_density,
            carrier_to_noise_density_dbhz=(
                carrier_to_noise_density
            ),
            ebn0_db=ebn0_db,
            required_ebn0_db=self.required_ebn0_db,
            link_margin_db=link_margin_db,
            ber=ber,
            propagation_delay_s=propagation_delay_s,
            link_available=link_margin_db >= 0.0,
        )