import datetime as dt
from typing import Any, Dict, Tuple, Union

import numpy as np
import pandas as pd

from simlib.agency.tariffs import Tariff
from simlib.custom_typing import IndexType, SignalType, UidType
from simlib.global_variables import CONTROL_KEY, ENERGY_KEY, POWER_KEY


class DataModule:
    def __init__(self) -> None:
        self.assets_historical_signal_data: Dict[
            UidType, Dict[IndexType, SignalType]
        ] = {}
        self.tariffs: Dict[UidType, Tariff] = {}

    def get_augmented_history(
        self, uid: Union[str, int], controls_power_mapping: Dict[int, float]
    ) -> pd.DataFrame:
        """Get the augmented history of the asset.

        Args:
            uid (int): The unique identifier of the asset.
            power_mapping (Dict[int, float]): A dictionary mapping
                                              the controls to power.

        Returns:
            pd.DataFrame: The augmented history of the asset.
        """
        df = self.get_asset_signal_history(uid)
        df = self.augment_df_with_all(uid, df, controls_power_mapping)
        return df

    def augment_df_with_all(
        self,
        uid: Union[str, int],
        df: pd.DataFrame,
        controls_power_mapping: Dict[int, float],
    ) -> pd.DataFrame:
        """Augment the dataframe with all the possible data."""
        df = self.augment_dataframe_with_virtual_metering_data(
            df.copy(), controls_power_mapping
        )
        df = self.augment_dataframe_with_tariff(df, uid)
        return df

    # --------------------------------------------------------------------------#
    # - ASSET SIGNAL DATA
    # --------------------------------------------------------------------------#
    def push_asset_signal_data(
        self,
        uid: Union[int, str],
        index: Union[int, dt.datetime],
        signals_dict: Dict[str, Union[float, int, str]],
    ) -> None:
        """Pushes a dictionary of signals to the asset's historical data.

        Args:
            uid (Union[int, str]): The unique identifier of the asset.
            index (Union[int, dt.datetime]): The index of the data.
            signals_dict (Dict[str, Union[float, int, str]]): A dictionary of
                                                              signals.
        """
        if uid not in self.assets_historical_signal_data:
            self.assets_historical_signal_data[uid] = {}

        # If the index already exists, update the data, else assign to it
        if index in self.assets_historical_signal_data[uid].keys():
            self.assets_historical_signal_data[uid][index].update(signals_dict)
        else:
            self.assets_historical_signal_data[uid][index] = signals_dict
        return None

    def get_asset_signal_history(self, uid: Union[int, str]) -> pd.DataFrame:
        data = self.assets_historical_signal_data[uid]
        df = pd.DataFrame.from_dict(data, orient="index")

        if CONTROL_KEY in df.columns:
            df[CONTROL_KEY] = df[CONTROL_KEY].astype("Int64")

        return df

    # --------------------------------------------------------------------------#
    # - VIRTUAL METER DATA
    # --------------------------------------------------------------------------#
    def augment_dataframe_with_virtual_metering_data(
        self, df: pd.DataFrame, control_power_mapping: Dict[int, float]
    ) -> pd.DataFrame:
        """Calculate the virtual metering data for the specified asset."""

        df = df.copy()

        # Power calculation
        if len(df) > 0 and CONTROL_KEY in df.columns:
            df[POWER_KEY] = df[CONTROL_KEY].map(control_power_mapping)

            # Energy calculation
            if isinstance(df.index, pd.DatetimeIndex):
                # Use an average delta value for missing deltas
                avg_delta = df.index.to_series().diff().mean()

                # If the delta does not exists (likely single row), no fill
                if avg_delta is pd.NaT:
                    time_diff = df.index.to_series().diff()
                # Else use average delta as value
                elif isinstance(avg_delta, dt.timedelta):
                    time_diff = (
                        df.index.to_series()
                        .diff()
                        .fillna(
                            pd.Timedelta(seconds=avg_delta.total_seconds())
                        )
                    )
                else:
                    raise ValueError(
                        f"Unknown avg_delta type: {type(avg_delta)}"
                    )
                energy = df[POWER_KEY] * time_diff.dt.seconds / 3600
            elif isinstance(df.index, int):
                time_diff = df.index.to_series().diff().fillna(0)
                energy = df[POWER_KEY] * time_diff
            else:
                raise ValueError("Unsupported index type.")

            df[ENERGY_KEY] = energy
        else:
            df[ENERGY_KEY] = np.nan
            df[POWER_KEY] = np.nan

        return df

    # --------------------------------------------------------------------------#
    # - TARIFF AND PRICING DATA
    # --------------------------------------------------------------------------#
    def assign_tariff_structure(
        self, uid: Union[int, str], tariff: Tariff
    ) -> None:
        """Assign a tariff to the specified asset.

        Args:
            tariff (Tariff): The tariff object to assign to this instance.
        """
        self.tariffs[uid] = tariff

    def augment_dataframe_with_tariff(
        self, df: pd.DataFrame, uid: Union[int, str]
    ) -> pd.DataFrame:
        """Augment the dataframe with tariff information.

        Args:
            df (pd.DataFrame): The dataframe to augment.
            uid (Union[int, str]): The unique identifier of the agent.

        Returns:
            pd.DataFrame: The augmented dataframe.
        """
        tariff = self.tariffs[uid]
        df = tariff.calculate_price_vector(df.copy())
        return df


def tf_all_cyclic(df: pd.DataFrame) -> pd.DataFrame:
    """Add all cyclic time features to the input dataframe"""
    df = tf_cyclic_day(df)
    df = tf_cyclic_weekday(df)
    df = tf_cyclic_month(df)
    df = tf_cyclic_year(df)
    return df


def tf_cyclic_day(df: pd.DataFrame) -> pd.DataFrame:
    """Incremental from 0 to 1 in 24 hours"""
    t = df.copy().index.hour + df.copy().index.minute / 60  # type: ignore
    df["tf_cos_d"], df["tf_sin_d"] = cyclic_time_features(t, 24)
    return df


def tf_1_hot_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """Adds 7 columns for each day of the week, and puts a 1 if it's that
    day.
    """
    day_indicator_columns = [
        "tf_mon",
        "tf_tue",
        "tf_wed",
        "tf_thu",
        "tf_fri",
        "tf_sat",
        "tf_sun",
    ]  # day of week indicators
    for i, ind_col in enumerate(day_indicator_columns):
        df[ind_col] = 0
        df.loc[df.index.dayofweek == i, ind_col] = 1  # type: ignore
    return df


def tf_cyclic_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """Incremental from 0 to 1 in 7 days"""
    t = df.copy().index.weekday  # type: ignore
    df["tf_cos_w"], df["tf_sin_w"] = cyclic_time_features(t, 7)
    return df


def tf_cyclic_month(df: pd.DataFrame) -> pd.DataFrame:
    """Incremental from 0 to 1 in month"""
    t = df.copy().index.day  # type: ignore
    period = df.copy().index.daysinmonth  # type: ignore
    df["tf_cos_m"], df["tf_sin_m"] = cyclic_time_features(t, period)
    return df


def tf_cyclic_year(df: pd.DataFrame) -> pd.DataFrame:
    """Incremental from 0 to 1 over the whole year"""
    t = df.copy().index.dayofyear - 1  # type: ignore
    df["tf_cos_y"], df["tf_sin_y"] = cyclic_time_features(t, 365)
    return df


def cyclic_time_features(t: Any, period: int) -> Tuple[Any, Any]:
    cos = np.cos(2 * t * np.pi / period)
    sin = np.sin(2 * t * np.pi / period)
    return (cos, sin)
