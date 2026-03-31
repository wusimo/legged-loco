# Legged Loco
This repo is used to train low-level locomotion policy of Unitree Go2 and H1 in Isaac Lab, with support for navigating Matterport3D indoor environments.

<p align="center">
<img src="./src/go2_teaser.gif" alt="First Demo" width="45%">
&emsp;
<img src="./src/h1_teaser.gif" alt="Second Demo" width="45%">
</p>


## Installation

### Prerequisites
- Ubuntu 22.04 or higher
- NVIDIA GPU with CUDA 12.1 support (tested on RTX 3090 24GB)
- Conda (Miniconda or Anaconda)

### Steps

1. Create a new conda environment with Python 3.10.
    ```shell
    conda create -n isaaclab python=3.10
    conda activate isaaclab
    ```

2. Install Isaac Sim 4.1.0. If you already have it via the Omniverse Launcher, skip this step. Otherwise install via pip:
    ```shell
    pip install isaacsim-rl==4.1.0 isaacsim-replicator==4.1.0 isaacsim-extscache-physics==4.1.0 isaacsim-extscache-kit-sdk==4.1.0 isaacsim-extscache-kit==4.1.0 isaacsim-app==4.1.0 --extra-index-url https://pypi.nvidia.com
    ```

3. Install PyTorch (**must** be installed after Isaac Sim to override its bundled version).
    ```shell
    pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cu121
    ```

4. Clone the Isaac Lab repository and link extensions.

    **Note**: This codebase was tested with Isaac Lab 1.1.0 and may not be compatible with newer versions. Please use the modified version of Isaac Lab provided below, which includes important bug fixes.
    ```shell
    git clone git@github.com:yang-zj1026/IsaacLab.git
    cd IsaacLab
    ln -s <THIS_REPO_DIR>/isaaclab_exts/omni.isaac.leggedloco source/extensions/omni.isaac.leggedloco
    ```

5. Run the Isaac Lab installer script and install rsl_rl.
    ```shell
    ./isaaclab.sh -i none
    ./isaaclab.sh -p -m pip install -e <THIS_REPO_DIR>/rsl_rl
    cd ..
    ```

6. Install additional dependencies for Matterport support.
    ```shell
    pip install usd-core trimesh s3transfer==0.10.0
    ```


## Usage

### Available Tasks

| Robot | Train | Play | Vision | Matterport |
|-------|-------|------|--------|------------|
| Go2 | `go2_base` | `go2_base_play` | `go2_vision` / `go2_vision_play` | `go2_matterport` / `go2_matterport_play` / `go2_matterport_dataset` |
| H1 | `h1_base` | `h1_base_play` | `h1_vision` / `h1_vision_play` | — |
| Go1 | `go1_base` | `go1_base_play` | `go1_vision` / `go1_vision_play` | — |
| G1 | `g1_base` | `g1_base_play` | `g1_vision` / `g1_vision_play` | — |

### Training

```shell
# Go2
python scripts/train.py --task go2_base --history_length 9 --run_name go2_run1 --max_iterations 2000 --save_interval 200 --headless

# H1
python scripts/train.py --task h1_base --run_name h1_run1 --max_iterations 2000 --save_interval 200 --headless
```

Checkpoints are saved to `logs/rsl_rl/<task>/<timestamp>_<run_name>/`.

### Evaluation (Play)

```shell
# Go2 (with video recording)
python scripts/play.py --task go2_base_play --history_length 9 --load_run <RUN_DIR> --num_envs 10 --headless --enable_cameras --video --video_length 500

# H1 (with video recording)
python scripts/play.py --task h1_base_play --load_run <RUN_DIR> --num_envs 10 --headless --enable_cameras --video --video_length 500
```

> **Note**: `--load_run` expects the full timestamped directory name (e.g., `2026-03-19_00-43-42_go2_run1`), not just the run name suffix. Use `--headless` for headless mode. Add `--enable_cameras --video` for video recording.


## Matterport3D Integration

The Matterport integration allows the Go2 robot to navigate inside real-world 3D scanned indoor environments from the [Matterport3D](https://niessner.github.io/Matterport/) dataset, following [R2R VLN-CE](https://github.com/jacobkrantz/VLN-CE) navigation episodes.

### Setup

#### 1. Prepare Matterport3D Scenes

Download scene GLB files from the [Matterport3D dataset](https://niessner.github.io/Matterport/) and convert them to USD format with collision meshes:

```python
import trimesh
from pxr import Usd, UsdGeom, UsdPhysics, Gf, Vt

SCENE_ID = "2azQ1b91cZZ"  # replace with your scene ID

scene = trimesh.load(f"path/to/{SCENE_ID}.glb", force='scene')
stage = Usd.Stage.CreateNew(f"assets/matterport_usd/{SCENE_ID}/{SCENE_ID}.usd")
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

Place the output USD files in `assets/matterport_usd/<SCENE_ID>/<SCENE_ID>.usd`.

#### 2. Prepare VLN-CE Navigation Data

Download the [R2R VLN-CE v1-3 preprocessed dataset](https://drive.google.com/file/d/1fo8F4NKgZDH-bPSdVU3cONAkt5EW-tyr/view?usp=sharing) and place it under:

```
assets/vln-ce/R2R_VLNCE_v1-3_preprocessed/
├── train/
│   ├── train.json.gz
│   └── train_gt.json.gz
```

If you only have a subset of scenes, filter the dataset to include only episodes from your available scenes and save as `train_filtered.json.gz`.

#### 3. Link Locomotion Checkpoint

The Matterport tasks reuse the Go2 base locomotion policy. Create a symlink so the matterport task can find it:

```shell
mkdir -p logs/rsl_rl/go2_matterport
ln -s <PATH_TO_GO2_BASE_CHECKPOINT_DIR>/* logs/rsl_rl/go2_matterport/
```

### Assets Directory Structure

```
assets/
├── matterport_usd/
│   ├── <SCENE_ID_1>/
│   │   └── <SCENE_ID_1>.usd
│   └── <SCENE_ID_2>/
│       └── <SCENE_ID_2>.usd
└── vln-ce/
    └── R2R_VLNCE_v1-3_preprocessed/
        └── train/
            ├── train.json.gz
            ├── train_gt.json.gz
            └── train_filtered.json.gz
```

### Running

#### Demo: Follow Expert Path

Runs the Go2 robot along an R2R expert navigation path using a PID controller:

```shell
python scripts/demo_matterport.py \
  --task go2_matterport \
  --history_length 9 \
  --load_run <RUN_DIR> \
  --episode_index 0 \
  --headless \
  --enable_cameras
```

Change `--episode_index` (0 to N-1) to run different navigation episodes from the filtered dataset.

#### Interactive Keyboard Control

Control the Go2 robot with WASD keys inside a Matterport scene (**requires a display**, cannot run headless):

```shell
python scripts/play_low_matterport_keyboard.py \
  --task go2_matterport \
  --history_length 9 \
  --load_run <RUN_DIR> \
  --scene_id <SCENE_ID>
```

#### Data Collection

Iterate over all episodes and collect navigation data:

```shell
python scripts/run_data_collection.py \
  --r2r_data_path assets/vln-ce/R2R_VLNCE_v1-3_preprocessed/train/train_filtered.json.gz \
  --task go2_matterport_dataset \
  --resume
```


## Add New Environments

You can add additional environments by placing config files under `isaaclab_exts/omni.isaac.leggedloco/omni/isaac/leggedloco/config/<robot_name>/` and registering them in the corresponding `__init__.py`. See `go2_matterport_cfg.py` for an example of extending a base locomotion config with scene loading and camera sensors.


## Troubleshooting

| Issue | Solution |
|-------|----------|
| `torch` version mismatch | Reinstall PyTorch **after** Isaac Sim: `pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cu121` |
| EULA not accepted | Run `./isaaclab.sh -i none` in the IsaacLab directory |
| Video recording fails | Add `--enable_cameras` flag |
| `s3transfer` import error | `pip install s3transfer==0.10.0` |
| `--load_run` not found | Use the full timestamped directory name (e.g., `2026-03-19_00-43-42_go2_run1`) |
| Model size mismatch | Ensure the task's observations match the training config exactly |
| Keyboard script fails headless | `play_low_matterport_keyboard.py` requires a display — do not use `--headless` |