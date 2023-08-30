import datetime as dt
import logging as log

from simlib.assets.energy_storage import EnergyStorage
from simlib.schemas.config import EnergyStorageConfig, EnergyStorageEfficiency
from simlib.schemas.state import EnergyStorageInternalState

# Execution and logging
log.basicConfig(level=log.WARNING)

# Asset
name = "example_energy_storage"
config = EnergyStorageConfig(
    initial_energy_wh=2e6,
    capacity_wh=3e6,
    action_power_mapping={1: -100000, 2: 0, 3: 100000},
    efficiency_in=EnergyStorageEfficiency(value=1.0),
    efficiency_out=EnergyStorageEfficiency(value=1.0),
)
energy_storage = EnergyStorage(name, config)

# Time variables
t = dt.datetime(2030, 1, 1, 0, 0, 0)
sim_end = dt.datetime(2030, 1, 7, 0, 0, 0)

# Simulation
initial_state = EnergyStorageInternalState(timestamp=t, internal_energy=2e6)
energy_storage.initialize(initial_state)
while t < sim_end:
    energy_storage.auto_step(t)
    t += dt.timedelta(minutes=60)

print(energy_storage.get_historical_data(True))
