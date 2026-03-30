import gymnasium as gym

from .go2_low_base_cfg import Go2BaseRoughEnvCfg, Go2BaseRoughEnvCfg_PLAY, Go2RoughPPORunnerCfg
from .go2_low_vision_cfg import Go2VisionRoughEnvCfg, Go2VisionRoughEnvCfg_PLAY, Go2VisionRoughPPORunnerCfg
from .go2_matterport_cfg import (
    Go2MatterportEnvCfg, Go2MatterportEnvCfg_PLAY, Go2MatterportDatasetEnvCfg, Go2MatterportPPORunnerCfg,
)

##
# Register Gym environments.
##

gym.register(
    id="go2_base",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2BaseRoughEnvCfg,
        "rsl_rl_cfg_entry_point": Go2RoughPPORunnerCfg,
    },
)


gym.register(
    id="go2_base_play",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2BaseRoughEnvCfg_PLAY,
        "rsl_rl_cfg_entry_point": Go2RoughPPORunnerCfg,
    },
)

gym.register(
    id="go2_vision",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2VisionRoughEnvCfg,
        "rsl_rl_cfg_entry_point": Go2VisionRoughPPORunnerCfg,
    },
)

gym.register(
    id="go2_vision_play",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2VisionRoughEnvCfg_PLAY,
        "rsl_rl_cfg_entry_point": Go2VisionRoughPPORunnerCfg,
    },
)

gym.register(
    id="go2_matterport",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2MatterportEnvCfg,
        "rsl_rl_cfg_entry_point": Go2MatterportPPORunnerCfg,
    },
)

gym.register(
    id="go2_matterport_play",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2MatterportEnvCfg_PLAY,
        "rsl_rl_cfg_entry_point": Go2MatterportPPORunnerCfg,
    },
)

gym.register(
    id="go2_matterport_dataset",
    entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": Go2MatterportDatasetEnvCfg,
        "rsl_rl_cfg_entry_point": Go2MatterportPPORunnerCfg,
    },
)