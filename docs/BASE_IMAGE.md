# Building the Base Image

This document explains how to build the base image locally or in CI.

## What is the Base Image?

The base image (`ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest`) contains:
- Python 3.11
- All dependencies from `requirements.txt`
- Pre-downloaded ML models (BERT Portuguese)
- Runtime libraries

It's built separately from the main application to:
- Speed up builds (15 min → 1-2 min)
- Reduce disk space usage (20GB → 2GB during builds)
- Only rebuild when dependencies change

## Automated Builds (CI)

The base image is automatically built by GitHub Actions when:
- `requirements.txt` changes
- `Dockerfile.base` changes
- Manually triggered via workflow dispatch

See: `.github/workflows/build_base_image.yaml`

## Manual Local Build

### Quick Start

```bash
# Run the automated script
./scripts/build_base_image_local.sh
```

The script will:
1. Set up Docker Buildx
2. Install QEMU for cross-platform builds
3. Ask if you want to push to registry or load locally
4. Build the image(s)

### Prerequisites

**Option 1: Docker Desktop** (Recommended - Easiest)
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Buildx and multi-arch support are included

**Option 2: Docker Engine on Linux**
```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com | sh

# Install Buildx plugin
mkdir -p ~/.docker/cli-plugins/
curl -L https://github.com/docker/buildx/releases/download/v0.12.0/buildx-v0.12.0.linux-amd64 \
  -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx

# Verify installation
docker buildx version
```

### Building for Both Architectures (amd64 + arm64)

**Option A: Push to Registry** (Builds both, requires registry access)

```bash
# 1. Login to GitHub Container Registry
docker login ghcr.io
# Username: your-github-username
# Password: your-github-personal-access-token

# 2. Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.base \
  --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
  --push \
  .
```

**Option B: Load Locally** (Builds only current platform)

```bash
# Build for your current architecture only
docker buildx build \
  --file Dockerfile.base \
  --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
  --load \
  .
```

**Note:** Docker buildx cannot load multi-arch images locally. You can only load one architecture at a time.

### Setting up Multi-Architecture Support

If you want to build for both amd64 and arm64:

```bash
# 1. Create a new buildx builder
docker buildx create --name multiarch --driver docker-container --use

# 2. Bootstrap the builder
docker buildx inspect --bootstrap

# 3. Install QEMU for cross-platform emulation
docker run --privileged --rm tonistiigi/binfmt --install all

# 4. Verify platforms available
docker buildx inspect multiarch
# Should show: Platforms: linux/amd64, linux/arm64, ...

# 5. Now you can build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.base \
  --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
  --push \
  .
```

## Testing the Base Image

After building, test that it works:

```bash
# Run a test command
docker run --rm ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
  python -c "import sentence_transformers; print('✅ Base image works!')"
```

## Building the Main Application Image

Once the base image exists, build the main application:

```bash
# This will use the base image and only copy application code
docker build -t my-app:latest -f Dockerfile .

# Should complete in 1-2 minutes (was 15 minutes before)
```

## Troubleshooting

### Error: "multiple platforms feature is currently not supported for docker driver"

You need to create a buildx builder:
```bash
docker buildx create --name multiarch --driver docker-container --use
```

### Error: "exec user process caused: exec format error"

You're trying to run an image built for a different architecture.
Either:
- Build for your current platform only (remove `--platform` flag)
- Or install QEMU: `docker run --privileged --rm tonistiigi/binfmt --install all`

### Build is very slow

Cross-platform builds (e.g., building arm64 on amd64) use QEMU emulation and are slower.
For faster builds:
- Build only for your current platform
- Or use a machine with the target architecture
- Or use GitHub Actions (builds natively on each platform)

### Out of disk space

The base image build requires ~20GB of free disk space.
Clean up Docker:
```bash
docker system prune -af --volumes
```

## GitHub Actions Secrets

To push images to GHCR from GitHub Actions, the workflow uses `GITHUB_TOKEN` which is automatically provided.

No manual secrets configuration is needed!

## Image Tags

The base image uses these tags:
- `latest` - Multi-arch manifest (points to latest-amd64 and latest-arm64)
- `latest-amd64` - AMD64/x86_64 architecture
- `latest-arm64` - ARM64/aarch64 architecture

## When to Rebuild

Rebuild the base image when:
- ✅ `requirements.txt` changes (new Python dependencies)
- ✅ ML model changes (different BERT model)
- ✅ Base OS dependencies change (apt packages in Dockerfile.base)
- ❌ Application code changes (use main Dockerfile, not base)

## Performance Comparison

| Metric | Without Base Image | With Base Image |
|--------|-------------------|-----------------|
| Build time | 15-20 min | 1-2 min |
| Disk space | ~20GB | ~2GB |
| Rebuild frequency | Every build | Only on dep changes |
| Cache effectiveness | Low (layers change) | High (base stable) |
