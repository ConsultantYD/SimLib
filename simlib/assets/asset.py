import datetime as dt
import json
from abc import ABCMeta, abstractmethod
from copy import copy
from os.path import join
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from simlib.global_variables import TIMESTAMP_KEY
from simlib.json_utils import serialize_instance
from simlib.schemas.control import ContinuousControl, DiscreteControl


class Asset(metaclass=ABCMeta):
    """Base class for all assets."""

    def __init__(self, name: str, config: Any) -> None:
        self.name = name
        self.config = config

        # Initialize internal simulation variables
        self.timestamp: Optional[Union[int, dt.datetime]] = None
        self.control: Optional[Union[int, float]] = None
        self.power: Optional[float] = None
        self.internal_energy: Optional[float] = None

        self.initialized: bool = False

        # Initialize history for variables tracked in the simulation
        tracked_variables = (
            self.config.tracked_variables + self.config.core_variables
        )
        self.history: Dict[str, List[Any]] = {
            variable_name: [] for variable_name in tracked_variables
        }

    @abstractmethod
    def initialize(self, initial_state: Any) -> None:
        """Initialize asset's initial state and values.

        Args:
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.
        """
        # Initialize internal variables
        for key, value in initial_state.to_dict().items():
            setattr(self, key, value)

        self._update_tracked_variables()

        # Initialize all internal variables with
        self.initialized = True

    @abstractmethod
    def step(
        self,
        control: Union[ContinuousControl, DiscreteControl],
        timestamp: Union[int, dt.datetime],
    ) -> Optional[float]:
        """Perform a step in the simulation, given a submitted control.
        This function must return the power consumption of the asset at
        this step step. Positive values indicate power consumption, while
        negative values indicate power generation.

        Args:
            control (int): control to be performed.
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.

        Returns:
            float: Power consumed by the asset.
        """
        if not self.initialized:
            raise ValueError("Asset must be initialized first.")
        self.timestamp = timestamp
        self.control = control.value
        self._update_tracked_variables()

        # NOTE: The child class must define the power variable
        return self.power

    @abstractmethod
    def auto_step(self, timestamp: Union[int, dt.datetime]) -> float:
        """Perform a step in the simulation, automatically choosing control.

        Args:
            timestamp (Union[int, dt.datetime]): timestamp of the simulation.

        Returns:
            float: Power consumed by the asset.
        """
        raise NotImplementedError

    def get_signal(self, signal: str) -> Any:
        return getattr(self, signal)

    def get_historical_data(self, nan_padding: bool = False) -> pd.DataFrame:
        """Returns a dataframe with all variables tracked in the simulation.

        Returns:
            pd.DataFrame: Dataframe with all variables tracked in simulation.
        """

        # Work with a copy of the data to avoid modifying the original
        data = copy(self.history)

        # Add None values to the end of the list to equalize length
        if nan_padding:
            max_length = max(len(value) for value in data.values())
            data_clean = {
                key: value + [None] * (max_length - len(value))
                for key, value in data.items()
            }

        # Remove last timestamps missing control and power data
        else:
            min_length = min(len(value) for value in data.values())
            data_clean = {
                key: value[:min_length] for key, value in data.items()
            }

        # Separate index column and clean data columns to create dataframe
        timestamp_data = data_clean.pop(TIMESTAMP_KEY)
        df = pd.DataFrame(data_clean, index=timestamp_data)
        return df

    def to_json(
        self, filename: Optional[str] = None, directory: str = ""
    ) -> None:
        """Save asset's attributes to a JSON file.

        Args:
            directory (str, optional): Save directory. Defaults to "".
        """
        filename = self.name if filename is None else filename
        filepath = join(directory, filename + ".json")
        with open(filepath, "w", encoding="utf-8") as f:
            attributes = vars(self)
            json.dump(
                attributes,
                f,
                ensure_ascii=False,
                indent=4,
                default=serialize_instance,
            )

    @classmethod
    def from_json(cls, filename: str, directory: str = "") -> "Asset":
        """Loads an asset's attributes from a JSON file.

        Args:
            directory (str, optional): Save directory. Defaults to "".
        """
        self = cls(name=filename, config=cls.get_default_config())
        filepath = join(directory, filename + ".json")
        with open(filepath, "r", encoding="utf-8") as f:
            attributes = json.load(f)
            for key, value in attributes.items():
                if hasattr(value, "pars_obj"):
                    setattr(self, key, value.parse_obj(value))
                else:
                    setattr(self, key, value)
        return self

    @staticmethod
    @abstractmethod
    def get_default_config() -> Any:
        """Returns the default config for the asset.

        Returns:
            Any: Default config for the asset.
        """
        raise NotImplementedError

    def _update_tracked_variables(self) -> None:
        tracked_variables = (
            self.config.tracked_variables + self.config.core_variables
        )
        for variable_name in tracked_variables:
            variable = getattr(self, variable_name)
            if variable is not None:
                self.history[variable_name].append(variable)
