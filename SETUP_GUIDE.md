# Legged-Loco Setup & Usage Guide

This guide covers the complete setup, training, evaluation, and Matterport integration for the legged-loco repository on this machine.

## Repository Locations

| Repository | Path |
|-----------|------|
| legged-loco | `/home/simo/Documents/vaNila/legged-loco/` |
| IsaacLab (fork) | `/home/simo/Documents/vaNila/IsaacLab/` |
| NaVILA (Matterport data source) | `/home/simo/Documents/vaNila/NaVILA/` |

---

## 1. Environment Setup

### Conda Environment

```bash
# Environment: isaaclab (Python 3.10)
source ~/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
```

### Installed Packages

| Package | Version |
|---------|---------|
| Python | 3.10 |
| Isaac Sim | 4.1.0 |
| PyTorch | 2.2.2+cu121 |
| IsaacLab | 1.1.0 (modified fork) |
| rsl_rl | 2.0.2 |
| GPU | NVIDIA RTX 3090 (24GB) |

### Installation Steps (already completed)

```bash
# 1. Create conda env
conda create -n isaaclab python=3.10 -y
conda activate isaaclab

# 2. Install Isaac Sim
pip install isaacsim-rl==4.1.0 isaacsim-replicator==4.1.0 \
  isaacsim-extscache-physics==4.1.0 isaacsim-extscache-kit-sdk==4.1.0 \
  isaacsim-extscache-kit==4.1.0 isaacsim-app==4.1.0 \
  --extra-index-url https://pypi.nvidia.com

# 3. Install PyTorch (MUST be after Isaac Sim to override its torch version)
pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cu121

# 4. Clone and setup IsaacLab
git clone https://github.com/yang-zj1026/IsaacLab.git
cd IsaacLab
ln -s /home/simo/Documents/vaNila/legged-loco/isaaclab_exts/omni.isaac.leggedloco \
  source/extensions/omni.isaac.leggedloco
./isaaclab.sh -i none

# 5. Install rsl_rl
./isaaclab.sh -p -m pip install -e /home/simo/Documents/vaNila/legged-loco/rsl_rl

# 6. Additional fixes applied
pip install usd-core trimesh        # for Matterport GLB->USD conversion
pip install s3transfer==0.10.0      # fix botocore conflict for video rendering
```

---

## 2. Available Robots & Tasks

### Registered Gym Environments

| Robot | Train Task | Play Task | Vision Task | Matterport Task |
|-------|-----------|-----------|-------------|-----------------|
| Go2 | `go2_base` | `go2_base_play` | `go2_vision` / `go2_vision_play` | `go2_matterport` / `go2_matterport_play` / `go2_matterport_dataset` |
| H1 | `h1_base` | `h1_base_play` | `h1_vision` / `h1_vision_play` | - |
| Go1 | `go1_base` | `go1_base_play` | `go1_vision` / `go1_vision_play` | - |
| G1 | `g1_base` | `g1_base_play` | `g1_vision` / `g1_vision_play` | - |

> **Note**: The README uses `--history_len` but the actual CLI flag is `--history_length`.

---

## 3. Training

All training commands should be run from the repo root:

```bash
cd /home/simo/Documents/vaNila/legged-loco
```

### Go2 Training

```bash
python scripts/train.py \
  --task=go2_base \
  --history_length=9 \
  --run_name=go2_run1 \
  --max_iterations=2000 \
  --save_interval=200 \
  --headless
```

- **Duration**: ~42 minutes on RTX 3090
- **Environments**: 4096 parallel
- **Checkpoints saved**: every 200 iterations + final

### H1 Training

```bash
python scripts/train.py \
  --task=h1_base \
  --run_name=h1_run1 \
  --max_iterations=2000 \
  --save_interval=200 \
  --headless
```

- **Duration**: ~47 minutes on RTX 3090
- **Environments**: 4096 parallel

### Training Results

| Robot | Total Time | Iterations | Timesteps | Terrain Level | Velocity Error (xy) |
|-------|-----------|------------|-----------|---------------|---------------------|
| Go2 | 42 min | 2000 | 196M | 5.69 | 0.205 |
| H1 | 47 min | 2000 | 262M | 5.80 | 0.188 |

### Saved Checkpoints

```
logs/rsl_rl/go2_base/2026-03-19_00-43-42_go2_run1/
  model_0.pt, model_200.pt, ..., model_1999.pt

logs/rsl_rl/h1_base_rough/2026-03-19_01-26-49_h1_run1/
  model_0.pt, model_200.pt, ..., model_1999.pt
```

---

## 4. Evaluation (Play)

### Go2 Evaluation

```bash
# Headless (no video)
python scripts/play.py \
  --task=go2_base_play \
  --history_length=9 \
  --load_run=2026-03-19_00-43-42_go2_run1 \
  --num_envs=10 \
  --headless

# With video recording
python scripts/play.py \
  --task=go2_base_play \
  --history_length=9 \
  --load_run=2026-03-19_00-43-42_go2_run1 \
  --num_envs=10 \
  --headless \
  --enable_cameras \
  --video \
  --video_length=500
```

### H1 Evaluation

```bash
python scripts/play.py \
  --task=h1_base_play \
  --load_run=2026-03-19_01-26-49_h1_run1 \
  --num_envs=10 \
  --headless \
  --enable_cameras \
  --video \
  --video_length=500
```

> **Important**: The `--load_run` argument must be the full timestamped directory name (e.g., `2026-03-19_00-43-42_go2_run1`), not just the run name suffix.

### Saved Outputs

| Output | Path |
|--------|------|
| Go2 video | `logs/rsl_rl/go2_base/2026-03-19_00-43-42_go2_run1/2026-03-19_00-43-42_go2_run1.mp4` |
| H1 video | `logs/rsl_rl/h1_base_rough/2026-03-19_01-26-49_h1_run1/2026-03-19_01-26-49_h1_run1.mp4` |
| Go2 JIT policy | `logs/rsl_rl/go2_base/2026-03-19_00-43-42_go2_run1/exported/policy.jit` |
| H1 JIT policy | `logs/rsl_rl/h1_base_rough/2026-03-19_01-26-49_h1_run1/exported/policy.jit` |

---

## 5. Matterport3D Integration

### Overview

The Matterport integration allows the Go2 robot to navigate inside real-world 3D scanned indoor environments from the Matterport3D dataset, following R2R VLN-CE navigation episodes.

### Available Scenes

| Scene ID | Source |
|----------|--------|
| `2azQ1b91cZZ` | From NaVILA repo |
| `QUCTc6BB5sX` | From NaVILA repo |

### Assets Directory Structure

```
assets/
├── matterport_usd/
│   ├── 2azQ1b91cZZ/
│   │   └── 2azQ1b91cZZ.usd      # converted from GLB, with collision meshes
│   └── QUCTc6BB5sX/
│       └── QUCTc6BB5sX.usd      # converted from GLB, with collision meshes
└── vln-ce/
    └── R2R_VLNCE_v1-3_preprocessed/
        └── train/
            ├── train.json.gz          # symlink to NaVILA data
            ├── train_gt.json.gz       # symlink to NaVILA data
            └── train_filtered.json.gz # 507 episodes from val_unseen for our 2 scenes
```

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `isaaclab_exts/.../config/go2/go2_matterport_cfg.py` | **Created** | Matterport environment config for Go2 |
| `isaaclab_exts/.../config/go2/__init__.py` | **Modified** | Registered `go2_matterport`, `go2_matterport_play`, `go2_matterport_dataset` gym envs |
| `scripts/demo_matterport.py` | **Modified** | Fixed f-string bug (line 288), `obj_filepath` -> `usd_path`, camera obs dict access |
| `scripts/play_low_matterport_keyboard.py` | **Modified** | Added `--scene_id` arg and matterport USD loading logic |
| `assets/matterport_usd/` | **Created** | USD scene files converted from GLB with collision meshes and default prims |
| `assets/vln-ce/` | **Created** | Filtered R2R dataset (507 episodes) with GT locations |
| `logs/rsl_rl/go2_matterport/` | **Created** | Symlink to go2_base checkpoint for matterport use |

### Matterport Config Details

The `Go2MatterportEnvCfg` (`go2_matterport_cfg.py`):
- Extends `Go2BaseRoughEnvCfg` with USD terrain loading
- Policy/critic observations match `go2_base` training for checkpoint compatibility
- Adds depth camera sensor (`RayCasterCameraCfg`) for visual data collection
- Adds `camera_obs` observation group for RGB/depth image capture
- Includes start/goal disk markers for visualization
- Disables terrain curriculum and domain randomization
- Sets 60-second episode length for navigation tasks
- Episode-specific fields (`expert_path`, `scene_id`, `instruction_text`, etc.) are set at runtime by the demo script

### Running the Matterport Demo

```bash
# Navigate a specific R2R episode in a Matterport scene
python scripts/demo_matterport.py \
  --task=go2_matterport \
  --history_length=9 \
  --load_run=2026-03-19_00-43-42_go2_run1 \
  --episode_index=0 \
  --headless \
  --enable_cameras
```

The demo script:
1. Loads an R2R VLN-CE episode from `train_filtered.json.gz`
2. Sets the robot start position/rotation from the episode data
3. Loads the corresponding Matterport USD scene
4. Uses a PID controller to follow the expert path waypoints
5. Captures RGB images and proprioceptive data at each step

Change `--episode_index` (0-506) to run different navigation episodes.

### Keyboard-Controlled Navigation (requires display)

```bash
# Default scene (2azQ1b91cZZ)
python scripts/play_low_matterport_keyboard.py \
  --task=go2_matterport \
  --history_length=9 \
  --load_run=2026-03-19_00-43-42_go2_run1

# Specify a different scene
python scripts/play_low_matterport_keyboard.py \
  --task=go2_matterport \
  --history_length=9 \
  --load_run=2026-03-19_00-43-42_go2_run1 \
  --scene_id=QUCTc6BB5sX
```

> This script requires a display/GUI (cannot run headless) — uses keyboard WASD for velocity commands.
> The `--scene_id` argument selects which Matterport scene to load (defaults to `2azQ1b91cZZ`).

### Data Collection

The `run_data_collection.py` script iterates over all episodes and calls `collect_data_matterport.py`:

```bash
python scripts/run_data_collection.py \
  --r2r_data_path=assets/vln-ce/R2R_VLNCE_v1-3_preprocessed/train/train_filtered.json.gz \
  --task=go2_matterport_dataset
```

> **Note**: `collect_data_matterport.py` is referenced but not included in the repository. The `demo_matterport.py` script serves the same purpose for individual episodes.

---

## 6. Adding New Scenes

To add more Matterport3D scenes:

### 1. Download scene GLB files

Place them at:
```
{NaVILA_repo}/evaluation/data/scene_datasets/mp3d/{SCENE_ID}/{SCENE_ID}.glb
```

### 2. Convert GLB to USD

```python
# Run with isaaclab conda env activated
import trimesh
from pxr import Usd, UsdGeom, UsdPhysics, Gf, Vt

scene = trimesh.load("path/to/{SCENE_ID}.glb", force='scene')
stage = Usd.Stage.CreateNew("assets/matterport_usd/{SCENE_ID}/{SCENE_ID}.usd")
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
root = UsdGeom.Xform.Define(stage, '/World')
stage.SetDefaultPrim(root.GetPrim())

for idx, (name, geom) in enumerate(scene.geometry.items()):
    if not isinstance(geom, trimesh.Trimesh):
        continue
    mesh = UsdGeom.Mesh.Define(stage, f"/World/mesh_{idx}")
    mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*v) for v in geom.vertices]))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([3] * len(geom.faces)))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(geom.faces.flatten().tolist()))
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    col = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
    col.GetApproximationAttr().Set("meshSimplification")

stage.GetRootLayer().Save()
```

### 3. Update filtered dataset

Re-run the filtering script to include episodes from the new scenes in `train_filtered.json.gz`.

---

## 7. Adding New Robot Environments

Place new config files under:
```
isaaclab_exts/omni.isaac.leggedloco/omni/isaac/leggedloco/config/{robot_name}/
```

Follow the pattern in existing configs (`go2_low_base_cfg.py`) and register in the corresponding `__init__.py`.

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| `torch` version mismatch | Reinstall: `pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cu121` |
| EULA not accepted | Run `echo "Yes" \| ./isaaclab.sh -i none` in IsaacLab directory |
| Video recording fails with `NO_GUI_OR_RENDERING` | Add `--enable_cameras` flag |
| `s3transfer` import error during video rendering | `pip install s3transfer==0.10.0` |
| `--load_run` not found | Use full timestamped directory name, not just the suffix |
| Model size mismatch loading checkpoint | Ensure env observations match the training config exactly |
| `terrain_generator.size` AttributeError | Disable terrain curriculum: `self.curriculum.terrain_levels = None` |
| Keyboard script fails headless | `play_low_matterport_keyboard.py` requires a display — cannot run with `--headless` |
| `collect_data_matterport.py` not found | This script is not included in the repo; use `demo_matterport.py` instead |
