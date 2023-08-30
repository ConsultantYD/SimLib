import datetime as dt
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Union

import pandas as pd

from simlib.custom_typing import UidType
from simlib.schemas.config import ModelEvaluationMetrics


class PredictionModel(metaclass=ABCMeta):
    def __init__(
        self, signal_inputs: Dict[str, int], signal_outputs: List[str]
    ) -> None:
        self.signal_inputs = signal_inputs
        self.signal_outputs = signal_outputs

    @abstractmethod
    def train(self, historical_signals: pd.DataFrame) -> None:
        raise NotImplementedError

    @abstractmethod
    def predict(
        self, signals_input: pd.DataFrame, new_index: Union[int, dt.datetime]
    ) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self, historical_signals: pd.DataFrame
    ) -> ModelEvaluationMetrics:
        raise NotImplementedError


class PredictionModule:
    def __init__(self) -> None:
        self.models: Dict[UidType, PredictionModel] = {}
        self.models_performance: Dict[
            UidType, List[ModelEvaluationMetrics]
        ] = {}

    def assign_model(
        self, uid: Union[int, str], model: PredictionModel
    ) -> None:
        """Assigns a model to the specified asset uid.

        Args:
            uid (Union[int, str]): The unique identifier of the asset.
            model (PredictionModel): The model object to assign to this
                                     instance.
        """
        self.models[uid] = model

    def train_model(
        self, uid: Union[int, str], historical_signals: pd.DataFrame
    ) -> None:
        """Train the model for the specified asset.

        Args:
            uid (Union[int, str]): The unique identifier of the asset.
            historical_signals (pd.DataFrame): The historical signals
                                               to train the model on.
        """
        self.models[uid].train(historical_signals)

    def get_model_prediction(
        self,
        uid: Union[int, str],
        signals_df: pd.DataFrame,
        new_index: Union[int, dt.datetime],
    ) -> pd.DataFrame:
        """Get the model's prediction for the specified asset.

        Args:
            uid (Union[int, str]): The unique identifier of the asset.
            signals_df (pd.DataFrame): The signals to predict from.
            new_index (Union[int, dt.datetime]): The index of the prediction.

        Returns:
            pd.DataFrame: The model's prediction.
        """

        prediction_df: pd.DataFrame = self.models[uid].predict(
            signals_df.copy(), new_index
        )
        return prediction_df

    def models_retraining_loop(self) -> None:
        pass
