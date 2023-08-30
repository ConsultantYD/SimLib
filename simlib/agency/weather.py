import datetime as dt

from meteostat import Hourly, Point  # type: ignore


class WeatherRef:
    """Weather data reference for the simulation, provides weather data
    based on true historical values at a target location."""

    def __init__(
        self, start: dt.datetime, end: dt.datetime, lat: float, lon: float, alt: float = 0
    ):
        """Initialise the weather reference, and prepare data based
        on the specified parameters.

        Args:
            start (dt.datetime): Start of the simulation.
            end (dt.datetime): End of the simulation.
            lat (float): Latitude of the target location.
            lon (float): Longitude of the target location.
            alt (float, optional): Altitude of the target location. Defaults to 0.
        """

        # Fetch historical weather data for specified location
        location = Point(lat=lat, lon=lon, alt=alt)
        retriever = Hourly(location, start, end)
        historical_hourly_data = retriever.fetch()

        # Interpolate data to 5 minutes interval
        self.data = historical_hourly_data.asfreq("5T").interpolate()[["temp"]]

    def get_temperature_at_time(self, time: dt.datetime) -> float:
        """GReturns the temperature at the specified time.

        Args:
            time (dt.datetime): The time to get the temperature at.

        Returns:
            float: The temperature at the specified time.
        """

        iloc_idx = self.data.index.get_indexer([time], method="nearest")
        temperature = float(self.data["temp"].iloc[iloc_idx].values[0])
        return temperature
