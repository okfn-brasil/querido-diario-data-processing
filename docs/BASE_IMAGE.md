# Building the Base Image

This document explains how to build the base image locally or in CI.

## What is the Base Image?

The base image (`ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest`) contains:
- Python 3.14 (slim)
- All runtime dependencies from `requirements.txt`
- PyTorch CPU-only build (sentence-transformers inference, no GPU needed)
- Pre-downloaded ML models (BERT Portuguese: `neuralmind/bert-base-portuguese-cased`)
- Runtime system libraries (`libpq5`, `libmagic1`)

It is built separately from the application image so that:
- Code-only changes rebuild in ~1 minute instead of 15–30 minutes
- Dependencies and models are cached independently of application code
- The base image is only rebuilt when `requirements.txt` or `Dockerfile.base` change

> **Note:** Development tools (`black`, `coverage`, `ruff`) live in
> `requirements-dev.txt` and are **not** installed in the production image.

## Automated Builds (CI)

The base image is automatically rebuilt by GitHub Actions when:
- `requirements.txt` changes
- `Dockerfile.base` changes
- Manually triggered via workflow dispatch

See: `.github/workflows/build_base_image.yaml`

## Manual Local Build

### Prerequisites

**Option 1: Docker Desktop** (recommended — buildx included)
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

**Option 2: Docker Engine on Linux**
```bash
# Install Buildx plugin
mkdir -p ~/.docker/cli-plugins/
curl -fsSL https://github.com/docker/buildx/releases/latest/download/buildx-linux-amd64 \
  -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
docker buildx version
```

### Quick Start

```bash
# Build base image for the current architecture and load locally
make build-base-multi-arch-load

# Build final application image and load locally
make build-multi-arch-load
```

### Available Make Targets

| Target | Description |
|--------|-------------|
| `make build-base-multi-arch-load` | Build base for current arch, load locally |
| `make build-base-multi-arch` | Build base for amd64+arm64, push to registry |
| `make build-multi-arch-load` | Build all images for current arch, load locally |
| `make build-multi-arch-optimized` | Build final image for amd64+arm64, push |
| `make build-multi-arch-tika-optimized` | Build Tika image for amd64+arm64, push |
| `make build-all-multi-arch` | Build everything for amd64+arm64, push |
| `make help-build` | Show all build targets with details |

### Building for Both Architectures (amd64 + arm64)

```bash
# 1. Login to GitHub Container Registry
docker login ghcr.io

# 2. Build and push base image for both architectures
make build-base-multi-arch

# 3. Build and push application image for both architectures
make build-multi-arch-optimized
```

The `REGISTRY` variable is automatically derived from the git remote:
```
git@github.com:okfn-brasil/repo.git  →  ghcr.io/okfn-brasil
```

Override if needed: `make build-base-multi-arch REGISTRY=my.registry/org`

### Setting up Multi-Architecture Support

```bash
# 1. Create a buildx builder
docker buildx create --name multiarch --driver docker-container --use

# 2. Bootstrap and install QEMU for cross-platform emulation
docker buildx inspect --bootstrap
docker run --privileged --rm tonistiigi/binfmt --install all

# 3. Verify available platforms
docker buildx inspect multiarch
# Should include: linux/amd64, linux/arm64
```

### Updating the Apache Tika Version

The Tika version is controlled by the `TIKA_VERSION` Make variable (default: `3.2.2`):

```bash
make build-tika-server TIKA_VERSION=3.3.0
make build-multi-arch-tika-optimized TIKA_VERSION=3.3.0
```

## Testing the Base Image

```bash
docker run --rm ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
  python -c "import sentence_transformers; print('Base image OK')"
```

## When to Rebuild

| Change | Rebuild needed |
|--------|---------------|
| `requirements.txt` | Base image |
| `Dockerfile.base` | Base image |
| Application code | Final image only |
| `requirements-dev.txt` | Neither (dev only) |
| `Dockerfile_apache_tika` | Tika image |

## Remote Build Cache

Multiarch builds use registry-based cache to speed up subsequent builds:

| Cache tag | Used by |
|-----------|---------|
| `…/base:base-buildcache` | `build-base-multi-arch` |
| `…/base:buildcache` | `build-multi-arch-optimized` |
| `…/tika:buildcache` | `build-multi-arch-tika-optimized` |

First build for each architecture: 20–30 min (amd64), up to 60 min (arm64 via QEMU).
Subsequent builds with warm cache: 5–10 min.

## Troubleshooting

### "multiple platforms feature is currently not supported for docker driver"
```bash
docker buildx create --name multiarch --driver docker-container --use
```

### "exec user process caused: exec format error"
You are running an image built for a different architecture. Install QEMU:
```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

### Out of disk space
```bash
docker system prune -af --volumes
```

### GitHub Actions — pushing to GHCR
The `GITHUB_TOKEN` is automatically provided; no extra secrets are needed.
