"""Matterport environment configuration for Go2 robot.

This config loads a Matterport3D USD scene as terrain and uses the Go2 vision
policy for locomotion within indoor environments.
"""

import numpy as np
from omni.isaac.lab.utils import configclass
import omni.isaac.lab.sim as sim_utils
from omni.isaac.lab.assets import ArticulationCfg, AssetBaseCfg
from omni.isaac.lab.managers import ObservationGroupCfg as ObsGroup
from omni.isaac.lab.managers import ObservationTermCfg as ObsTerm
from omni.isaac.lab.managers import RewardTermCfg as RewTerm
from omni.isaac.lab.managers import EventTermCfg as EventTerm
from omni.isaac.lab.managers import SceneEntityCfg
from omni.isaac.lab.terrains import TerrainImporterCfg
from omni.isaac.lab.scene import InteractiveSceneCfg
from omni.isaac.lab.sensors import ContactSensorCfg, RayCasterCfg, patterns, RayCasterCameraCfg
from omni.isaac.lab.actuators import ImplicitActuatorCfg, DelayedPDActuatorCfg
from omni.isaac.lab.utils.assets import ISAAC_NUCLEUS_DIR, ISAACLAB_NUCLEUS_DIR
from omni.isaac.lab.utils.noise import AdditiveUniformNoiseCfg as Unoise
from omni.isaac.lab.envs import ManagerBasedRLEnvCfg
from omni.isaac.lab_tasks.manager_based.locomotion.velocity.velocity_env_cfg import (
    ActionsCfg, CurriculumCfg, RewardsCfg, EventCfg, CommandsCfg,
)
from omni.isaac.lab.managers import TerminationTermCfg as DoneTerm

import omni.isaac.leggedloco.leggedloco.mdp as mdp
from omni.isaac.lab_tasks.utils.wrappers.rsl_rl import (
    RslRlOnPolicyRunnerCfg,
    RslRlPpoActorCriticCfg,
    RslRlPpoAlgorithmCfg,
)

from .go2_low_base_cfg import Go2BaseRoughEnvCfg, Go2RoughPPORunnerCfg, UNITREE_GO2_CFG


@configclass
class Go2MatterportPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    num_steps_per_env = 24
    max_iterations = 5000
    save_interval = 50
    experiment_name = "go2_matterport"
    empirical_normalization = False
    policy = RslRlPpoActorCriticCfg(
        init_noise_std=1.0,
        actor_hidden_dims=[512, 256, 128],
        critic_hidden_dims=[512, 256, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.01,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=1.0e-3,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
    )


##
# Scene definition for Matterport environments
##
@configclass
class Go2MatterportSceneCfg(InteractiveSceneCfg):
    """Configuration for matterport scene with Go2 robot."""

    # ground terrain - will be overridden with USD file path at runtime
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="usd",
        usd_path="placeholder.usd",  # overridden per episode
        collision_group=-1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
        debug_vis=False,
    )

    # robots
    robot: ArticulationCfg = UNITREE_GO2_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # start/goal disk markers
    disk_1 = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/StartDisk",
        spawn=sim_utils.CylinderCfg(
            radius=0.3,
            height=0.02,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 1.0, 0.0)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0)),
    )
    disk_2 = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/GoalDisk",
        spawn=sim_utils.CylinderCfg(
            radius=0.3,
            height=0.02,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.0, 0.0)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0)),
    )

    # sensors
    height_scanner = RayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
        attach_yaw_only=True,
        pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=[3.0, 2.0]),
        debug_vis=False,
        mesh_prim_paths=["/World/ground"],
    )
    depth_sensor = RayCasterCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Head_lower",
        offset=RayCasterCameraCfg.OffsetCfg(pos=(0.28945, 0.0, -0.046), rot=(0.389, 0.0, 0.921, 0.0)),
        attach_yaw_only=False,
        pattern_cfg=patterns.PinholeCameraPatternCfg(
            focal_length=1.88,
            horizontal_aperture=3.6,
            height=120,
            width=160,
        ),
        debug_vis=False,
        mesh_prim_paths=["/World/ground"],
    )
    contact_forces = ContactSensorCfg(prim_path="{ENV_REGEX_NS}/Robot/.*", history_length=3, track_air_time=True)

    # lights
    sky_light = AssetBaseCfg(
        prim_path="/World/skyLight",
        spawn=sim_utils.DomeLightCfg(
            intensity=750.0,
            texture_file=f"{ISAAC_NUCLEUS_DIR}/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr",
        ),
    )


##
# Rewards
##
@configclass
class Go2MatterportRewardsCfg(RewardsCfg):
    termination_penalty = RewTerm(func=mdp.is_terminated, weight=-200.0)
    hip_deviation = RewTerm(
        func=mdp.joint_deviation_l1,
        weight=-0.4,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=[".*_hip_joint"])},
    )
    joint_deviation = RewTerm(
        func=mdp.joint_deviation_l1,
        weight=-0.04,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=[".*_thigh_joint", ".*_calf_joint"])},
    )
    base_height = RewTerm(
        func=mdp.base_height_l2,
        weight=-5.0,
        params={"target_height": 0.32},
    )
    action_smoothness = RewTerm(
        func=mdp.action_smoothness_penalty,
        weight=-0.02,
    )
    joint_power = RewTerm(
        func=mdp.power_penalty,
        weight=-2e-5,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=".*")},
    )
    collision = RewTerm(
        func=mdp.collision_penalty,
        weight=-5.0,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names=["Head.*", ".*_hip", ".*_thigh", ".*_calf"]),
            "threshold": 0.1,
        },
    )


##
# Terminations
##
@configclass
class Go2MatterportTerminationsCfg:
    """Termination terms for the MDP."""
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=["base"]), "threshold": 1.0},
    )
    bad_orientation = DoneTerm(
        func=mdp.bad_orientation,
        params={"limit_angle": 1.0},
    )


##
# Observations
##
@configclass
class Go2MatterportObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy group - matches go2_base training obs."""
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(n_min=-0.2, n_max=0.2))
        base_rpy = ObsTerm(func=mdp.base_rpy, noise=Unoise(n_min=-0.1, n_max=0.1))
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        joint_pos = ObsTerm(func=mdp.joint_pos_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(n_min=-1.5, n_max=1.5))
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    @configclass
    class ProprioCfg(ObsGroup):
        """Proprioceptive observations (used by history wrapper)."""
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(n_min=-0.2, n_max=0.2))
        base_rpy = ObsTerm(func=mdp.base_rpy, noise=Unoise(n_min=-0.1, n_max=0.1))
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        joint_pos = ObsTerm(func=mdp.joint_pos_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(n_min=-1.5, n_max=1.5))
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    @configclass
    class CriticObsCfg(ObsGroup):
        """Critic observations - matches go2_base training critic obs."""
        base_lin_vel = ObsTerm(func=mdp.base_lin_vel, noise=Unoise(n_min=-0.1, n_max=0.1))
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(n_min=-0.2, n_max=0.2))
        projected_gravity = ObsTerm(
            func=mdp.projected_gravity,
            noise=Unoise(n_min=-0.05, n_max=0.05),
        )
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        joint_pos = ObsTerm(func=mdp.joint_pos_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(n_min=-1.5, n_max=1.5))
        actions = ObsTerm(func=mdp.last_action)
        height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("height_scanner")},
            clip=(-1.0, 1.0),
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class CameraObsCfg(ObsGroup):
        """Camera observations for data collection."""
        camera_obs = ObsTerm(
            func=mdp.matterport_raycast_camera_data,
            params={"sensor_cfg": SceneEntityCfg("depth_sensor"), "data_type": "distance_to_image_plane"},
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    # observation groups
    policy: PolicyCfg = PolicyCfg()
    proprio: ProprioCfg = ProprioCfg()
    critic: CriticObsCfg = CriticObsCfg()
    camera_obs: CameraObsCfg = CameraObsCfg()


##
# Environment Configuration
##
@configclass
class Go2MatterportEnvCfg(Go2BaseRoughEnvCfg):
    """Configuration for Go2 in Matterport3D environments."""

    scene: Go2MatterportSceneCfg = Go2MatterportSceneCfg(num_envs=1, env_spacing=0.0)
    observations: Go2MatterportObservationsCfg = Go2MatterportObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    rewards: RewardsCfg = Go2MatterportRewardsCfg()
    terminations: Go2MatterportTerminationsCfg = Go2MatterportTerminationsCfg()

    # Episode-specific fields set at runtime by the demo script
    expert_path: np.ndarray = np.zeros((1, 3))
    expert_path_length: int = 1
    expert_time: np.ndarray = np.zeros(1)
    goals: list = None
    episode_id: int = 0
    scene_id: str = ""
    traj_id: int = 0
    instruction_text: str = ""
    instruction_tokens: list = None
    reference_path: np.ndarray = np.zeros((1, 3))

    def __post_init__(self):
        """Post initialization."""
        super().__post_init__()

        # update sensor periods
        self.scene.height_scanner.update_period = self.sim.dt * self.decimation
        self.scene.depth_sensor.update_period = self.sim.dt * self.decimation

        # velocity command ranges for indoor navigation
        self.commands.base_velocity.ranges.lin_vel_x = (-0.0, 0.5)
        self.commands.base_velocity.ranges.lin_vel_y = (0.0, 0.0)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.5, 0.5)

        # disable terrain-based reset (robot starts at specified position)
        self.events.reset_base = EventTerm(
            func=mdp.reset_root_state_uniform,
            mode="reset",
            params={
                "pose_range": {"x": (-0.0, 0.0), "y": (-0.0, 0.0), "yaw": (-0.0, 0.0)},
                "velocity_range": {
                    "x": (0.0, 0.0),
                    "y": (0.0, 0.0),
                    "z": (0.0, 0.0),
                    "roll": (0.0, 0.0),
                    "pitch": (0.0, 0.0),
                    "yaw": (0.0, 0.0),
                },
            },
        )

        # disable domain randomization for matterport
        self.events.base_external_force_torque = None
        self.events.push_robot = None
        self.events.actuator_gains = None

        # disable terrain curriculum (no terrain generator in matterport)
        self.curriculum.terrain_levels = None

        self.episode_length_s = 60.0  # longer episodes for navigation


@configclass
class Go2MatterportEnvCfg_PLAY(Go2MatterportEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 1
        self.observations.policy.enable_corruption = False


@configclass
class Go2MatterportDatasetEnvCfg(Go2MatterportEnvCfg):
    """Configuration for data collection in Matterport environments."""
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 1
