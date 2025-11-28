# Pull latest base image to ensure fresh cache for app builds
docker pull ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest

docker buildx build \
       --platform linux/amd64,linux/arm64 \
       --file Dockerfile.base \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --cache-to type=inline \
       --push \
       .

docker buildx build \
       --platform linux/amd64 \
       --file Dockerfile.base \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest-amd64 \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --push \
       .

# Build and push ARM64-specific tag
docker buildx build \
       --platform linux/arm64 \
       --file Dockerfile.base \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest-arm64 \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --push \
       .

# Pull latest base image to ensure fresh cache for app builds
docker pull ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest
docker pull ghcr.io/okfn-brasil/querido-diario-data-processing:latest

# Build for both architectures and create manifest with multi-arch latest tag
docker buildx build \
       --platform linux/amd64,linux/arm64 \
       --file Dockerfile \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing:latest \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing:latest \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --cache-to type=inline \
       --push \
       .

# Build and push AMD64-specific tag
docker buildx build \
       --platform linux/amd64 \
       --file Dockerfile \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing:latest-amd64 \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing:latest \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --push \
       .

# Build and push ARM64-specific tag
docker buildx build \
       --platform linux/arm64 \
       --file Dockerfile \
       --tag ghcr.io/okfn-brasil/querido-diario-data-processing:latest-arm64 \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing:latest \
       --cache-from type=registry,ref=ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest \
       --push \
       .
