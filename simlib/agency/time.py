import datetime as dt
from typing import Union


class TimeModule:
    def __init__(self, time_utc: dt.datetime) -> None:
        """Initialise the time module.

        Args:
            time_utc (dt.datetime): The initial time, in UTC.
        """
        self.time_utc = time_utc

    def get_time_utc(self) -> dt.datetime:
        """Get the current time, in UTC.

        Returns:
            dt.datetime: Current time, in UTC
        """
        return self.time_utc

    def increment_time(self, delta: Union[dt.timedelta, int]) -> None:
        """Increment the current time by the specified delta.

        Args:
            delta (Union[dt.timedelta, int]): The delta to increment
            the time by. Integers will be converted to seconds.
        """
        if isinstance(delta, int):
            delta = dt.timedelta(seconds=delta)
        self.time_utc += delta
