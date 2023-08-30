import datetime as dt
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from simlib.global_variables import ENERGY_KEY, TARIFF_KEY


class Tariff(metaclass=ABCMeta):
    @abstractmethod
    def calculate_price(
        self,
        time: Optional[dt.datetime] = None,
        power: Optional[float] = None,
        energy: Optional[float] = None,
        other_info: Dict[str, Any] = {},
    ) -> Optional[float]:
        raise NotImplementedError

    @abstractmethod
    def calculate_price_vector(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class FlatRateTariff(Tariff):
    def __init__(self, rate: float = 0.1):
        self.rate = rate

    def calculate_price(
        self,
        time: Optional[dt.datetime] = None,
        power: Optional[float] = None,
        energy: Optional[float] = None,
        other_info: Dict[str, Any] = {},
    ) -> Optional[float]:
        if energy is not None:
            return self.rate * energy
        return None

    def calculate_price_vector(self, df: pd.DataFrame) -> pd.DataFrame:
        df[TARIFF_KEY] = df[ENERGY_KEY].values * self.rate  # type: ignore
        return df


class HydroQuebecDTariff(Tariff):
    def __init__(
        self,
        patrimonial_value: float = 0.06509,
        highest_value: float = 0.10041,
        cuttoff_energy_value: float = 40.0,
    ):
        self.patrimonial_value = patrimonial_value
        self.highest_value = highest_value
        self.cuttoff_energy_value = cuttoff_energy_value

    def calculate_price(
        self,
        time: Optional[dt.datetime] = None,
        power: Optional[float] = None,
        energy: Optional[float] = None,
        other_info: Dict[str, Any] = {},
    ) -> Optional[float]:
        if energy is not None:
            period_energy = (
                0 if "period_energy" not in other_info.keys() else other_info["period_energy"]
            )
            low_consumption_energy = min(self.cuttoff_energy_value, period_energy)
            high_consumption_energy = max(energy - self.cuttoff_energy_value, 0)
            price = float(
                low_consumption_energy * self.patrimonial_value
                + high_consumption_energy * self.highest_value
            )
            return price
        return None

    @abstractmethod
    def calculate_price_vector(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class OntarioTOUTariff(Tariff):
    def __init__(
        self,
        on_peak: float = 0.151,
        mid_peak: float = 0.102,
        off_peak: float = 0.074,
        on_peak_range: Tuple[int, int] = (17, 19),
        mid_peak_ranges: Tuple[Tuple[int, int], Tuple[int, int]] = ((7, 11), (17, 19)),
    ):
        self.on_peak = on_peak
        self.mid_peak = mid_peak
        self.off_peak = off_peak
        self.on_peak_range = on_peak_range
        self.mid_peak_ranges = mid_peak_ranges

    def calculate_price(
        self,
        time: Optional[dt.datetime] = None,
        power: Optional[float] = None,
        energy: Optional[float] = None,
        other_info: Dict[str, Any] = {},
    ) -> Optional[float]:
        if time is not None and energy is not None:
            hour = time.hour

            # Apply Ontario's TOU based on 24h
            if self.on_peak_range[1] > hour >= self.on_peak_range[0]:
                return self.on_peak * energy / 1000  #
            if (
                self.mid_peak_ranges[0][1] > hour >= self.mid_peak_ranges[0][0]
                or self.mid_peak_ranges[1][1] > hour >= self.mid_peak_ranges[1][0]
            ):
                return self.mid_peak * energy / 1000
            return self.off_peak * energy / 1000
        return None

    def calculate_price_vector(self, df: pd.DataFrame) -> pd.DataFrame:
        # TODO: Update with ranges like method above
        # t = df.copy().index.hour

        # # Apply Ontario's TOU based on 24h
        # s = np.ones(df.shape[0]) * self.off_peak
        # s[(t >= 11) & (t < 17)] = self.on_peak
        # s[((t >= 17) & (t < 19)) | ((t >= 7) & (t < 11))] = self.mid_peak

        # # Add energy cost to original dataframe
        # df[TARIFF_KEY] = df[ENERGY_KEY].values * s
        return df
