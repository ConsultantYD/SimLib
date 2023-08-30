import os
from typing import Callable

from simlib.agency.agent import Agent
from simlib.assets.energy_storage import EnergyStorage
from simlib.schemas.config import EnergyStorageConfig


def test_agent_save_and_load(
    make_energy_storage: Callable[[str, EnergyStorageConfig], EnergyStorage]
) -> None:
    energy_storage = make_energy_storage()  # type: ignore
    agent = Agent(uid="test_agent")
    agent.assign_to_asset(energy_storage)
    agent.to_file()

    new_agent = Agent.from_file("test_agent")
    assert new_agent.uid == "test_agent"
    assert vars(new_agent.asset) == vars(energy_storage)
    os.remove("test_agent")
