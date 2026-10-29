# BONES-SEED Viewer

本 fork 的本機功能與開發進度見 [PROGRESS.md](PROGRESS.md)：SSD 壓縮資料直接播放、VRM 重定向、Kimodo 動作匯入與生成介面整合。索引與驗證工具見 [tools/local/README.md](tools/local/README.md)。

A web application for browsing the BONES-SEED motion capture dataset. Renders skeleton animations on 3D character models in the browser using Three.js, with a searchable file browser, metadata panel, and temporal label overlay.

Supports two character models: 
* [SOMA body model](https://github.com/NVlabs/SOMA-X) 
* Unitree G1 robot

Temporal labels were created by NVIDIA for the [Kimodo](https://research.nvidia.com/labs/sil/projects/kimodo/) project.

## Quick Start

Requires [Docker](https://docs.docker.com/get-docker/) (includes Docker Compose).

```bash
git clone <repo-url>
cd seed-viewer

cp .env.example .env
# Edit .env — set DATA_PATH to your extracted BONES-SEED dataset root

./shdocker.sh          # Linux / macOS
# or
docker compose up --build   # any platform
```

The app will be available at **http://localhost:8666**.

### Dataset Structure

`DATA_PATH` should point to the root of the extracted dataset:

```
DATA_PATH/
  metadata/               # Parquet metadata + jsonl temporal labels
  soma_proportional/bvh/  # Original mocap on SOMA — BVH files
  soma_uniform/bvh/       # Mocap retargeted to unified SOMA shape — BVH files
  g1/csv/                 # Mocap retargeted to G1 robot — MuJoCo compatible CSV files
  soma_shapes/			      # SOMA shape parameters
```

## Local Development

For development without Docker:

- Node.js 20.10.0 (see `.nvmrc`)
- Python 3.11
- [PDM](https://pdm-project.org/) for Python dependencies

**Backend** (terminal 1):
```bash
cd backend
pdm install
DATA_ROOT=/path/to/dataset PORT=8080 python src/main.py
```

**Frontend** (terminal 2):
```bash
cd frontend
npm install
npm run dev    # Vite dev server on localhost:5173, proxies /api → localhost:8080
```

## Testing

End-to-end tests use Playwright against the running app at `http://localhost:8666`:

```bash
cd frontend
npx playwright install   # first time only
npx playwright test      # headless Chromium
npx playwright test --headed   # with visible browser
```

## SOMA Example

The `soma/` directory contains a minimal Python example for parsing BONES-SEED motion capture data and running it through the SOMA body model.

## Related Work

BONES-SEED is part of a larger effort to enable humanoid motion data for robotics, physical AI, and other applications.

Check out these related works:

* [SOMA Body Model](https://github.com/NVlabs/SOMA-X) - Parametric human body model with standardized skeleton, mesh, and shape parameters
* [SOMA Retargeter]()
* [GEM-X](https://github.com/NVlabs/GEM-X) - Human motion estimation from video
* [Kimodo](https://research-staging.nvidia.com/labs/sil/projects/kimodo/) - Kinematic motion diffusion model for text and constraint-driven 3D human and robot motion generation
* [ProtoMotions](https://github.com/NVlabs/ProtoMotions) - GPU-accelerated simulation and learning framework for training physically simulated digital humans and humanoid robots
* [SONIC](https://nvlabs.github.io/GEAR-SONIC/) - Whole-body control for humanoid robots, training locomotion and interaction policies


## License

Apache 2.0 — see [LICENSE](LICENSE).
