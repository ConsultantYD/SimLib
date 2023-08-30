from typing import Any, Dict, List

from pydantic import field_validator

from simlib.global_variables import CONTROL_KEY, POWER_KEY, TIMESTAMP_KEY

from .base import BaseSchema


# ----------------------------------------------------------------------------
# ASSET CONFIG
# ----------------------------------------------------------------------------
class AssetConfig(BaseSchema):
    core_variables: List[str] = [TIMESTAMP_KEY, CONTROL_KEY, POWER_KEY]
    initial_state_dict: Dict[str, Any] = {}


# ENERGY STORAGE ASSET
class EnergyStorageEfficiencyLimits:
    UPPER_LIMIT: float = 1.0
    LOWER_LIMIT: float = 0.0


class EnergyStorageEfficiency(BaseSchema):
    value: float = 1.0

    @field_validator("value")
    def check_value(cls, v: float) -> float:  # pylint: disable=no-self-argument
        if (
            v > EnergyStorageEfficiencyLimits.UPPER_LIMIT
            or v < EnergyStorageEfficiencyLimits.LOWER_LIMIT
        ):
            raise ValueError("Efficiency must be between 0 and 1.")
        return v


class EnergyStorageConfig(AssetConfig):
    capacity_wh: float = 3e6
    initial_energy_wh: float = 2e6
    control_power_mapping: Dict[int, float] = {1: -100000, 2: 0, 3: 100000}
    efficiency_in: EnergyStorageEfficiency = EnergyStorageEfficiency()
    efficiency_out: EnergyStorageEfficiency = EnergyStorageEfficiency()
    decay_factor: float = 1.0
    tracked_variables: List[str] = ["internal_energy"]


# ----------------------------------------------------------------------------
# PREDICTION MODULE CONFIGS
# ----------------------------------------------------------------------------
class ModelEvaluationMetrics(BaseSchema):
    root_mean_squared_error: float
    mean_absolute_error: float
    mean_squared_error: float


# ----------------------------------------------------------------------------
# AGENT CONFIGS
# ----------------------------------------------------------------------------
class AgentDataConfig(BaseSchema):
    controls_power_mapping: Dict[int, float]
    tracked_signals: List[str]
    signals_metadata: Dict[str, Any] = {}
    signals_tags: Dict[str, List[str]] = {}


class AgentPredictionConfig(BaseSchema):
    signal_inputs: Dict[str, int]  # Signal inputs with their history length (0 = t)
    signal_outputs: List[str]  # Signals output to predict


class AgentControlConfig(BaseSchema):
    trajectory_length: int = 6


class AgentConfig(BaseSchema):
    control: AgentControlConfig
    data: AgentDataConfig
    prediction: AgentPredictionConfig


# ----------------------------------------------------------------------------
# SIMULATION CONFIGS
# ----------------------------------------------------------------------------
class SimulationTimeConfig(BaseSchema):
    start_time: str = "2023-01-01 00:00:00"
    end_time: str = "2023-01-07 00:00:00"
    step_size_s: int = 300


class SimulationGeographicalConfig(BaseSchema):
    location_lat: float
    location_lon: float
    location_alt: float = 0.0


class SimulationAssetConfig(BaseSchema):
    n_energy_storages: int


class SimulationGlobalConfig(BaseSchema):
    filepath: str = ""
    time: SimulationTimeConfig
    geography: SimulationGeographicalConfig
    assets: SimulationAssetConfig
