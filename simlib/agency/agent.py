import datetime as dt
import os
from typing import Any, Dict, List, Union

import dill  # type: ignore
import numpy as np
import pandas as pd

from simlib.global_variables import CONTROL_KEY


class Agent:
    """Agent class, with one instance per asset and driving the
    framework's logic."""

    def __init__(self, uid: Union[str, int]) -> None:
        """Initialise the agent.

        Args:
            uid (Union[str, int]): The unique identifier of the agent.
        """
        self.uid = uid

        # Initialize the future agent's attributes as None
        self.asset = None
        self.modules: Dict[str, Any] = {}
        self.index = None
        self.previous_index = None
        self.trajectories_list: List[pd.DataFrame] = []

    def run(self) -> None:
        self.sample_asset_signals()

        # Initialize important variables
        time_now = self.modules["time"].get_time_utc()
        config = self.modules["config"].get_agent_config(uid=self.uid)
        controls_power_mapping = config.data.controls_power_mapping
        history_df = self.modules["data"].get_augmented_history(
            self.uid, controls_power_mapping
        )

        # Trajectories simulation
        n_trajectories = 1
        trajectory_len = config.control.trajectory_length
        self.trajectories_list = []
        for _ in range(n_trajectories):
            trajectory = self._sample_trajectory(
                history_df, controls_power_mapping, trajectory_len, time_now
            )
            self.trajectories_list.append(trajectory)

    def get_controls(self) -> Any:
        return None

    def get_asset_signals_history(self) -> pd.DataFrame:
        df: pd.DataFrame = self.modules["data"].get_asset_signal_history(
            self.uid
        )
        return df

    def assign_to_asset(self, asset: Any) -> None:
        self.asset = asset

    def update_modules_references(self, modules: Any) -> None:
        self.modules = modules

    def to_file(self, directory: str = "") -> None:
        """Save the agent's state to the specified directory.

        Args:
            directory (str): The directory to save the agent to.
        """
        filepath = os.path.join(directory, f"{self.uid}")
        with open(filepath, "wb") as f:
            dill.dump(vars(self), f)

    @classmethod
    def from_file(cls, uid: Union[str, int], directory: str = "") -> "Agent":
        """Load an agent from the specified directory.

        Args:
            uid (Union[str, int]): The unique identifier of the agent.
            directory (str): The directory to load the agent from.
        """
        filepath = os.path.join(directory, f"{uid}")
        with open(filepath, "rb") as f:
            internal_variables = dill.load(f)
        self = cls(uid)
        self.__dict__.update(internal_variables)
        return self

    def sample_asset_signals(self) -> None:
        if self.asset is not None:
            # Keep track of current and previous index
            self.previous_index = self.index
            self.index = self.modules["time"].get_time_utc()

            # Store the current normal signal values
            config = self.modules["config"].get_agent_config(uid=self.uid)
            signals_dict = {
                signal: self.asset.get_signal(signal)
                for signal in config.data.tracked_signals
                if signal is not None
            }
            self.modules["data"].push_asset_signal_data(
                self.uid, self.index, signals_dict
            )

            # The control we sample is actually the one from prev time step
            if self.previous_index is not None:
                control_dict = {
                    CONTROL_KEY: self.asset.get_signal(CONTROL_KEY)
                }
                self.modules["data"].push_asset_signal_data(
                    self.uid, self.previous_index, control_dict
                )
        else:
            raise ValueError("No asset associated to this agent.")

    # TODO: Add int index compatibility, and parameterize sim time step
    def _sample_trajectory(
        self,
        history_df: pd.DataFrame,
        controls_power_mapping: Dict[int, float],
        trajectory_len: int,
        time_now: dt.datetime,
    ) -> pd.DataFrame:
        # Work with a copy of the input dataframe
        df = history_df.copy()

        # Create trajectory sample
        current_idx = time_now
        for _ in range(trajectory_len):
            next_idx = current_idx + dt.timedelta(minutes=5)
            u = int(np.random.randint(1, 4))
            df.loc[current_idx, "control"] = u
            df = self.modules["prediction"].get_model_prediction(
                self.uid, df, next_idx
            )
            df = self.modules["data"].augment_df_with_all(
                self.uid, df, controls_power_mapping
            )
            current_idx = next_idx

        return df
