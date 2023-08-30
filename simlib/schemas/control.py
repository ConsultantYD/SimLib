from dataclasses import dataclass

from .base import BaseSchema


# ----------------------------------------------------------------------------
# CONTROL TYPES
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class DiscreteControl(BaseSchema):
    value: int


@dataclass(frozen=True)
class ContinuousControl(BaseSchema):
    value: float
