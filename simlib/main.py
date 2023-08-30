from simlib.schemas.config import (
    SimulationAssetConfig,
    SimulationGeographicalConfig,
    SimulationGlobalConfig,
    SimulationTimeConfig,
)
from simlib.simulation import Simulation

if __name__ == "__main__":
    sim_config = SimulationGlobalConfig(
        time=SimulationTimeConfig(
            start_time="2023-01-01 00:00:00",
            end_time="2023-01-01 02:00:00",
            step_size_s=300,
        ),
        geography=SimulationGeographicalConfig(
            location_lat=43.6532, location_lon=-79.3832, location_alt=76
        ),
        assets=SimulationAssetConfig(n_energy_storages=1),
    )

    simulation = Simulation(sim_config)
    simulation.run()
