import datetime as dt

import pandas as pd

from simlib.agency.agent import Agent
from simlib.agency.config import ConfigModule
from simlib.agency.data import DataModule
from simlib.agency.prediction import PredictionModel, PredictionModule
from simlib.agency.tariffs import FlatRateTariff
from simlib.agency.time import TimeModule
from simlib.agency.weather import WeatherRef
from simlib.assets.energy_storage import EnergyStorage
from simlib.schemas.config import (
    AgentConfig,
    AgentControlConfig,
    AgentDataConfig,
    AgentPredictionConfig,
    EnergyStorageConfig,
    EnergyStorageEfficiency,
    ModelEvaluationMetrics,
    SimulationAssetConfig,
    SimulationGeographicalConfig,
    SimulationGlobalConfig,
    SimulationTimeConfig,
)
from simlib.schemas.state import EnergyStorageInternalState


class EnergyStorageModel(PredictionModel):
    def train(self, historical_signals: pd.DataFrame) -> None:
        pass

    def predict(self, signals_input: pd.DataFrame, new_index: int | dt.datetime) -> pd.DataFrame:
        E = signals_input.loc[signals_input.index[-1], "internal_energy"]
        u: int = signals_input.loc[signals_input.index[-1], "control"]
        power_map = {1: -100000, 2: 0, 3: 100000}
        power = power_map[u]
        dE = power * 300 / 3600

        output_df = signals_input.copy()
        output_df.loc[new_index, "internal_energy"] = E + dE

        return output_df

    def evaluate(self, historical_signals: pd.DataFrame) -> ModelEvaluationMetrics:
        return ModelEvaluationMetrics(
            root_mean_squared_error=0, mean_absolute_error=0, mean_squared_error=0
        )


class Simulation:
    def __init__(self, simulation_config: SimulationGlobalConfig) -> None:
        # Store configuration
        self.config = simulation_config

        # Global time variables
        self.start_time = dt.datetime.strptime(
            self.config.time.start_time,
            "%Y-%m-%d %H:%M:%S",
        )
        self.end_time = dt.datetime.strptime(
            self.config.time.end_time,
            "%Y-%m-%d %H:%M:%S",
        )

        # Initialization process
        self._initialize_modules_and_references()
        self._initialize_assets()
        self._initialize_agents()

    def run(self) -> None:
        # Simulation time loop
        while self.time_module.get_time_utc() < self.end_time:
            # NOTE: The order is important - Agents, assets then time
            # Run agents
            for agent in self.agents:
                agent.run()

            # Update assets
            for asset in self.assets:
                asset.auto_step(self.time_module.get_time_utc())

            # Increment simulation time
            self.time_module.increment_time(self.config.time.step_size_s)

    def _initialize_modules_and_references(self) -> None:
        # Time
        self.time_module = TimeModule(time_utc=self.start_time)

        # Weather
        self.weather_ref = WeatherRef(
            lat=self.config.geography.location_lat,
            lon=self.config.geography.location_lon,
            alt=self.config.geography.location_alt,
            start=self.start_time,
            end=self.end_time,
        )

        # Data Modules
        self.data_module = DataModule()

        # Configuration Module
        self.config_module = ConfigModule()

        # Prediction Module
        self.prediction_module = PredictionModule()

        # Create internal modules reference
        self.modules = {
            "config": self.config_module,
            "data": self.data_module,
            "prediction": self.prediction_module,
            "time": self.time_module,
        }

    def _initialize_assets(self) -> None:
        es_config = EnergyStorageConfig(
            initial_energy_wh=2e6,
            capacity_wh=3e6,
            action_power_mapping={1: -100000, 2: 0, 3: 100000},
            efficiency_in=EnergyStorageEfficiency(value=1.0),
            efficiency_out=EnergyStorageEfficiency(value=1.0),
        )

        n_assets = self.config.assets.n_energy_storages
        self.assets = [
            EnergyStorage(f"energy_storage_{i}", es_config) for i in range(1, n_assets + 1)
        ]

        # Initialize assets with their initial state
        initial_state = EnergyStorageInternalState(timestamp=self.start_time, internal_energy=2e6)
        for energy_storage in self.assets:
            energy_storage.initialize(initial_state)

    def _initialize_agents(self) -> None:
        # Create agent configs
        agent_config = AgentConfig(
            control=AgentControlConfig(
                trajectory_length=6,
            ),
            data=AgentDataConfig(
                controls_power_mapping={1: -100000, 2: 0, 3: 100000},
                tracked_signals=["internal_energy"],
            ),
            prediction=AgentPredictionConfig(
                signal_inputs={"internal_energy": 0, "control": 0},
                signal_outputs=["internal_energy"],
            ),
        )

        # Define each agent's configuration
        for i in range(1, len(self.assets) + 1):
            self.config_module.push_new_agent_config(uid=i, agent_config=agent_config)

        # Create agents
        self.agents = [Agent(i) for i in range(1, len(self.assets) + 1)]

        # Update modules with agent references and informations
        model = EnergyStorageModel(None, None)  # type: ignore
        for i, agent in enumerate(self.agents):
            agent.assign_to_asset(self.assets[i])
            self.modules["data"].assign_tariff_structure(  # type: ignore
                uid=i + 1, tariff=FlatRateTariff()
            )
            self.modules["prediction"].assign_model(uid=i + 1, model=model)  # type: ignore
            agent.update_modules_references(self.modules)


if __name__ == "__main__":
    sim_config = SimulationGlobalConfig(
        time=SimulationTimeConfig(
            start_time="2023-01-01 00:00:00", end_time="2023-01-01 02:00:00", step_size_s=300
        ),
        geography=SimulationGeographicalConfig(
            location_lat=43.6532, location_lon=-79.3832, location_alt=76
        ),
        assets=SimulationAssetConfig(n_energy_storages=1),
    )

    simulation = Simulation(sim_config)
    simulation.run()
