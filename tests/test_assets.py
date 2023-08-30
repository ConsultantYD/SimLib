import os
from typing import Callable

from simlib.assets.energy_storage import EnergyStorage
from simlib.global_variables import CONTROL_KEY, TIMESTAMP_KEY
from simlib.schemas.config import EnergyStorageConfig, EnergyStorageEfficiency
from simlib.schemas.control import DiscreteControl
from simlib.schemas.state import EnergyStorageInternalState


def test_energy_storage_creation() -> None:
    name = "test_energy_storage"
    config = EnergyStorageConfig(
        initial_energy_wh=2e6,
        capacity_wh=3e6,
        action_power_mapping={1: -100000, 2: 0, 3: 100000},
        efficiency_in=EnergyStorageEfficiency(value=1.0),
        efficiency_out=EnergyStorageEfficiency(value=1.0),
    )
    energy_storage = EnergyStorage(name, config)
    assert energy_storage.name == name
    assert config == energy_storage.config


def test_energy_storage_not_initialized(
    make_energy_storage: Callable[[str, EnergyStorageConfig], EnergyStorage]
) -> None:
    energy_storage = make_energy_storage()  # type: ignore

    try:
        energy_storage.step(timestamp=0, control=DiscreteControl(2))
    except ValueError:
        pass


def test_energy_storage_simulation(
    make_energy_storage: Callable[[str, EnergyStorageConfig], EnergyStorage]
) -> None:
    energy_storage = make_energy_storage()  # type: ignore
    initial_state = EnergyStorageInternalState(timestamp=0, internal_energy=2e6)
    energy_storage.initialize(initial_state)
    for i in range(1, 4):
        energy_storage.step(timestamp=i, control=DiscreteControl(2))

    assert energy_storage.history[TIMESTAMP_KEY] == [0, 1, 2, 3]
    assert energy_storage.history[CONTROL_KEY] == [2, 2, 2]


def test_energy_storage_save_and_load(
    make_energy_storage: Callable[[str, EnergyStorageConfig], EnergyStorage]
) -> None:
    energy_storage = make_energy_storage()  # type: ignore
    initial_state = EnergyStorageInternalState(timestamp=0, internal_energy=2e6)
    energy_storage.initialize(initial_state)
    for i in range(1, 4):
        energy_storage.step(timestamp=i, control=DiscreteControl(2))

    energy_storage.to_json("test_name")

    new_energy_storage = EnergyStorage.from_json("test_name")

    assert new_energy_storage.history[TIMESTAMP_KEY] == [0, 1, 2, 3]
    assert new_energy_storage.history[CONTROL_KEY] == [2, 2, 2]

    os.remove("test_name.json")


def test_energy_storage_historical_data(
    make_energy_storage: Callable[[str, EnergyStorageConfig], EnergyStorage]
) -> None:
    energy_storage = make_energy_storage()  # type: ignore
    initial_state = EnergyStorageInternalState(timestamp=0, internal_energy=2e6)
    energy_storage.initialize(initial_state)
    for i in range(1, 4):
        energy_storage.step(timestamp=i, control=DiscreteControl(2))

    # Test on dataframe equalized with no NaNs
    df = energy_storage.get_historical_data(nan_padding=False)
    assert df.index.tolist() == [0, 1, 2]
    assert df["internal_energy"].tolist() == [2e6, 2e6, 2e6]
