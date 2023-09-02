from abc import ABCMeta, abstractmethod

import pandas as pd

from simlib.global_variables import POWER_KEY, REWARD_KEY


class Product(metaclass=ABCMeta):
    """Base class for all assets."""

    @abstractmethod
    def calculate_reward(self, df: pd.DataFrame) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def get_reward_name(self) -> str:
        return REWARD_KEY


class DemandResponseProduct(Product):
    def calculate_reward(self, df: pd.DataFrame) -> list[float]:
        df = df.copy()
        df[REWARD_KEY] = -df[POWER_KEY].values  # type: ignore
        df.loc[
            (df.index.hour < 17) | (df.index.hour >= 18), REWARD_KEY  # type: ignore # noqa: E501
        ] = 0
        return df[REWARD_KEY].values.tolist()

    def get_reward_name(self) -> str:
        return REWARD_KEY + "_DR"
