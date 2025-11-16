#!/usr/bin/env bash
# Script to build and push the main application image for both amd64 and arm64

set -e

echo "=============================================================================="
echo "Building Multi-Architecture Application Image"
echo "=============================================================================="

# Configuration
REPO="ghcr.io/okfn-brasil/querido-diario-data-processing"
BASE_IMAGE="${REPO}/base:latest"
APP_IMAGE="${REPO}"
PLATFORMS="linux/amd64,linux/arm64"

echo ""
echo "Application Image: ${APP_IMAGE}:latest"
echo "Base Image: ${BASE_IMAGE}"
echo "Platforms: ${PLATFORMS}"
echo ""

# Check if Docker Buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo "❌ Docker Buildx is not available. Please install it first."
    exit 1
fi

# Check if buildx builder exists
echo "Checking buildx builder..."
if ! docker buildx inspect multiarch >/dev/null 2>&1; then
    echo "Creating buildx builder 'multiarch'..."
    docker buildx create --name multiarch --driver docker-container --use
    docker buildx inspect --bootstrap
else
    echo "Using existing buildx builder 'multiarch'..."
    docker buildx use multiarch
fi

# Verify base image exists
echo ""
echo "Verifying base image exists..."
if ! docker buildx imagetools inspect ${BASE_IMAGE} >/dev/null 2>&1; then
    echo "❌ Base image not found: ${BASE_IMAGE}"
    echo ""
    echo "You need to build the base image first:"
    echo "  ./scripts/build_base_image_local.sh"
    echo ""
    echo "Or wait for CI to build it automatically."
    exit 1
fi
echo "✅ Base image found: ${BASE_IMAGE}"

# Check registry login
echo ""
echo "Checking registry login..."
if ! docker login ghcr.io --get-login >/dev/null 2>&1; then
    echo "Attempting to login to GitHub Container Registry..."
    if ! docker login ghcr.io; then
        echo "❌ Login failed. Please login first:"
        echo "  docker login ghcr.io"
        echo ""
        echo "Use your GitHub username and a Personal Access Token with packages:write scope"
        exit 1
    fi
fi
echo "✅ Logged in to ghcr.io"

# Ask for confirmation
echo ""
echo "=============================================================================="
echo "This will build the application image for amd64 and arm64."
echo "Expected time: 1-2 minutes (using pre-built base image)"
echo "=============================================================================="
read -p "Do you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Build cancelled."
    exit 0
fi

# Ask for version tag
echo ""
echo "Choose image tag:"
echo "1) latest (default)"
echo "2) Custom version (e.g., v1.0.0)"
echo ""
read -p "Enter choice (1 or 2): " -n 1 -r TAG_CHOICE
echo

TAGS=""
if [[ $TAG_CHOICE == "2" ]]; then
    echo ""
    read -p "Enter version tag (e.g., v1.0.0): " VERSION_TAG
    if [[ -z "$VERSION_TAG" ]]; then
        echo "❌ Version tag cannot be empty"
        exit 1
    fi
    TAGS="--tag ${APP_IMAGE}:${VERSION_TAG} --tag ${APP_IMAGE}:${VERSION_TAG}-amd64 --tag ${APP_IMAGE}:${VERSION_TAG}-arm64"
    echo "Building with tags: ${VERSION_TAG}, ${VERSION_TAG}-amd64, ${VERSION_TAG}-arm64"
else
    TAGS="--tag ${APP_IMAGE}:latest --tag ${APP_IMAGE}:latest-amd64 --tag ${APP_IMAGE}:latest-arm64"
    echo "Building with tags: latest, latest-amd64, latest-arm64"
fi

# Build and push
echo ""
echo "=============================================================================="
echo "Building and pushing application image..."
echo "=============================================================================="
echo ""

docker buildx build \
    --platform ${PLATFORMS} \
    --file Dockerfile \
    ${TAGS} \
    --push \
    .

BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=============================================================================="
    echo "✅ Build completed successfully!"
    echo "=============================================================================="
    echo ""
    echo "Images available at:"
    if [[ $TAG_CHOICE == "2" ]]; then
        echo "  - ${APP_IMAGE}:${VERSION_TAG} (multi-arch)"
        echo "  - ${APP_IMAGE}:${VERSION_TAG}-amd64"
        echo "  - ${APP_IMAGE}:${VERSION_TAG}-arm64"
    else
        echo "  - ${APP_IMAGE}:latest (multi-arch)"
        echo "  - ${APP_IMAGE}:latest-amd64"
        echo "  - ${APP_IMAGE}:latest-arm64"
    fi
    echo ""
    echo "Test the image:"
    if [[ $TAG_CHOICE == "2" ]]; then
        echo "  docker run --rm ${APP_IMAGE}:${VERSION_TAG} python --version"
    else
        echo "  docker run --rm ${APP_IMAGE}:latest python --version"
    fi
    echo ""
else
    echo ""
    echo "=============================================================================="
    echo "❌ Build failed!"
    echo "=============================================================================="
    echo ""
    echo "Check the error messages above for details."
    echo ""
    exit 1
fi
