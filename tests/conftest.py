from typing import Callable

import pytest

from simlib.assets.energy_storage import EnergyStorage
from simlib.schemas.config import EnergyStorageConfig, EnergyStorageEfficiency


@pytest.fixture(scope="module")
def make_energy_storage() -> (
    Callable[[str, EnergyStorageConfig], EnergyStorage]
):
    def make(
        name: str = "test_energy_storage",
        config: EnergyStorageConfig = EnergyStorageConfig(
            initial_energy_wh=2e6,
            capacity_wh=3e6,
            action_power_mapping={1: -100000, 2: 0, 3: 100000},
            efficiency_in=EnergyStorageEfficiency(value=1.0),
            efficiency_out=EnergyStorageEfficiency(value=1.0),
        ),
    ) -> EnergyStorage:
        return EnergyStorage(name, config)

    return make
