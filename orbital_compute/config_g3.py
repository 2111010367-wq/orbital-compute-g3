"""
Configuración técnica del proyecto Grupo 3.

Proyecto:
Arquitectura cognitiva de control distribuido para satélites
autónomos en formación mediante inteligencia artificial federada,
comunicaciones inter-satélite de alta frecuencia y optimización
energética en tiempo real.
"""

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

PROJECT_NAME = "Arquitectura Cognitiva G3"
NUM_SATELLITES = 3

LEADER_ID = "SAT-000"
FOLLOWER_1_ID = "SAT-001"
FOLLOWER_2_ID = "SAT-002"

SATELLITE_IDS = [
    LEADER_ID,
    FOLLOWER_1_ID,
    FOLLOWER_2_ID,
]


# ============================================================
# 2. CONFIGURACIÓN ORBITAL
# ============================================================

ORBIT_ALTITUDE_KM = 550.0
ORBIT_INCLINATION_DEG = 53.0

EARTH_RADIUS_KM = 6378.137
EARTH_GRAVITATIONAL_PARAMETER_KM3_S2 = 398600.4418


# ============================================================
# 3. FORMACIÓN LÍDER-SEGUIDOR
# Sistema de referencia LVLH:
# x: radial
# y: dirección de vuelo
# z: normal al plano orbital
# ============================================================

DESIRED_SEPARATION_M = 1000.0

FOLLOWER_1_DESIRED_POSITION_M = (0.0, 1000.0, 0.0)
FOLLOWER_2_DESIRED_POSITION_M = (0.0, -1000.0, 0.0)

MAX_FORMATION_ERROR_M = 20.0

# Ganancias preliminares del controlador PD
FORMATION_KP = 2.0e-5
FORMATION_KD = 8.0e-3

# Máxima aceleración de control admisible
MAX_CONTROL_ACCELERATION_M_S2 = 1.0e-3


# ============================================================
# 4. ENLACE INTER-SATÉLITE DE ALTA FRECUENCIA
# Escenario académico en banda Ka
# ============================================================

ISL_FREQUENCY_GHZ = 28.0
ISL_BITRATE_BPS = 10_000_000.0

TX_POWER_W = 2.0
TX_ANTENNA_GAIN_DBI = 20.0
RX_ANTENNA_GAIN_DBI = 20.0

TX_LOSSES_DB = 1.0
RX_LOSSES_DB = 1.0
POINTING_LOSS_DB = 1.0
POLARIZATION_LOSS_DB = 0.5

SYSTEM_NOISE_TEMPERATURE_K = 500.0
MIN_EBN0_DB = 8.0


# ============================================================
# 5. SISTEMA ENERGÉTICO PRELIMINAR
# Los valores serán calibrados posteriormente.
# ============================================================

SOLAR_POWER_W = 30.0
BATTERY_CAPACITY_WH = 60.0

INITIAL_SOC = 0.80
MINIMUM_SOC = 0.30
CRITICAL_SOC = 0.20

HOUSEKEEPING_POWER_W = 8.0
ISL_COMMUNICATION_POWER_W = 5.0
FEDERATED_TRAINING_POWER_W = 12.0
CONTROL_SYSTEM_POWER_W = 3.0


# ============================================================
# 6. RESTRICCIONES TÉRMICAS
# ============================================================

MAX_OPERATION_TEMPERATURE_C = 50.0
CRITICAL_TEMPERATURE_C = 60.0


# ============================================================
# 7. APRENDIZAJE FEDERADO
# ============================================================

FEDERATED_ALGORITHM = "FedAvg"
FEDERATED_ROUNDS = 10
LOCAL_EPOCHS = 1
MIN_FEDERATED_PARTICIPANTS = 2

MODEL_SIZE_MB = 5.0
GRADIENT_COMPRESSION_RATIO = 0.10


# ============================================================
# 8. SIMULACIÓN
# ============================================================

SIMULATION_DURATION_S = 3600.0
TIME_STEP_S = 1.0

ENABLE_FORMATION_CONTROL = True
ENABLE_RF_ISL = True
ENABLE_ENERGY_MANAGEMENT = True
ENABLE_FEDERATED_LEARNING = True
ENABLE_COGNITIVE_SUPERVISOR = True