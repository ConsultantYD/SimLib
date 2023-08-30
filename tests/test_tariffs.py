import pandas as pd
import pytest

from simlib.agency.tariffs import FlatRateTariff
from simlib.global_variables import ENERGY_KEY, TARIFF_KEY


def test_flat_rate_tariff() -> None:
    df = pd.DataFrame({ENERGY_KEY: [1, 2, 3]})
    tariff = FlatRateTariff(rate=0.1)

    energy = 8
    price = tariff.calculate_price(energy=energy)
    assert price == 0.8

    df_updated = tariff.calculate_price_vector(df)
    assert pytest.approx(df_updated[TARIFF_KEY].values.tolist()) == [
        0.1,
        0.2,
        0.3,
    ]
