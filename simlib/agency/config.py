from typing import Dict, Union

from simlib.custom_typing import UidType
from simlib.schemas.config import AgentConfig, AgentPredictionConfig


class ConfigModule:
    def __init__(self) -> None:
        self.agent_configs: Dict[UidType, AgentConfig] = {}
        self.prediction_configs: Dict[UidType, AgentPredictionConfig] = {}

    # -----------------------------------------------------------------------
    # AGENT
    # -----------------------------------------------------------------------
    # TODO: Add validation process when pushing new configs
    def push_new_agent_config(
        self, uid: Union[str, int], agent_config: AgentConfig
    ) -> None:
        self.agent_configs[uid] = agent_config

    def get_agent_config(self, uid: Union[str, int]) -> AgentConfig:
        return self.agent_configs[uid]
