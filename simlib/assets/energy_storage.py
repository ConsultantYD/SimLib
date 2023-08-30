import datetime as dt
import logging as log
from random import randint
from typing import Union

from simlib.assets.asset import Asset
from simlib.schemas.config import EnergyStorageConfig
from simlib.schemas.control import ContinuousControl, DiscreteControl
from simlib.schemas.state import EnergyStorageInternalState


class EnergyStorage(Asset):
    def __init__(self, name: str, config: EnergyStorageConfig):
        self.history = {}
        super().__init__(name, config)
        self.internal_energy: float = self.config.initial_energy_wh

    def initialize(self, initial_state: EnergyStorageInternalState) -> None:
        """Initialize asset's initial state and values.

        Args:
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.
        """
        super().initialize(initial_state)

    def step(
        self,
        control: Union[ContinuousControl, DiscreteControl],
        timestamp: Union[int, dt.datetime],
    ) -> float:
        """Perform a step in the simulation, given a submitted control.

        Args:
            control (DiscreteControl): control to be performed.
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.
        """
        # Continuous not supported yet
        if isinstance(control, ContinuousControl):
            raise NotImplementedError("Continuous controls not supported yet.")

        # Get power associated with inputed control
        self.power = self.config.control_power_mapping[control.value]
        self.power = 0 if self.power is None else self.power  # Linting

        # Previous timestamp from last step
        previous_timestamp = self.timestamp

        # Case 1 - Integer timestamp
        if isinstance(timestamp, int) and isinstance(previous_timestamp, int):
            timestamp_difference = timestamp - previous_timestamp
            energy_difference = self.power * timestamp_difference
        # Case 2 - Datetime timestamp
        elif isinstance(timestamp, dt.datetime) and isinstance(
            previous_timestamp, dt.datetime
        ):
            time_difference = timestamp - previous_timestamp
            energy_difference = (
                self.power * time_difference.total_seconds() / 3600
            )
        # Case 3 - Unknown or inconsistent timestamp type
        else:
            raise ValueError(
                f"timestamp type not supported: {type(timestamp)}."
            )

        # Update energy
        self.internal_energy += energy_difference

        # Log
        log.debug(
            f"{self.name} | Step: {timestamp} | "
            f"Power: {self.power} W. | "
            f"Internal energy: {self.internal_energy} Wh."
        )

        # Run base class to store variables of interest
        super().step(control, timestamp)

        return self.power

    def auto_step(self, timestamp: Union[int, dt.datetime]) -> float:
        """Perform a step in the simulation, automatically choosing control.

        Args:
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.
        """
        control_value = randint(
            min(list(self.config.control_power_mapping.keys())),
            max(list(self.config.control_power_mapping.keys())),
        )
        control = DiscreteControl(control_value)
        return self.step(control, timestamp)

    def get_state_of_charge(self) -> float:
        """Get state of charge (SoC), in %, of the energy storage."""
        state_of_charge: float = (
            self.internal_energy / self.config.capacity_wh
        ) * 100
        return round(state_of_charge, 2)

    @staticmethod
    def get_default_config() -> EnergyStorageConfig:
        return EnergyStorageConfig()
