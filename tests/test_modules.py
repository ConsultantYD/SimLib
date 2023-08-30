import datetime as dt

from simlib.agency.time import TimeModule
from simlib.agency.weather import WeatherRef


def test_weather_ref() -> None:
    # Toronto location
    weather_ref = WeatherRef(
        lat=43.6532,
        lon=-79.3832,
        alt=76,
        start=dt.datetime(2023, 1, 1),
        end=dt.datetime(2023, 1, 2),
    )
    temp = weather_ref.get_temperature_at_time(
        dt.datetime(2023, 1, 1, 0, 2, 0)
    )
    assert temp == 6.2


def test_time_module() -> None:
    start = dt.datetime(2023, 1, 1)
    time_module = TimeModule(time_utc=start)

    time_module.increment_time(dt.timedelta(minutes=60))
    assert time_module.time_utc == dt.datetime(2023, 1, 1, 1, 0, 0)
    assert time_module.get_time_utc() == dt.datetime(2023, 1, 1, 1, 0, 0)
