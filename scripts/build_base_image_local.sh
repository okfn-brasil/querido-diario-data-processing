#!/usr/bin/env bash
# Script to build and push the base image locally for both amd64 and arm64

set -e

echo "=============================================================================="
echo "Building Multi-Architecture Base Image Locally"
echo "=============================================================================="

# Configuration
REPO="ghcr.io/okfn-brasil/querido-diario-data-processing"
IMAGE_NAME="base"
PLATFORMS="linux/amd64,linux/arm64"

echo ""
echo "Image: ${REPO}/${IMAGE_NAME}:latest"
echo "Platforms: ${PLATFORMS}"
echo ""

# Check if Docker Buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo "❌ Docker Buildx is not available. Please install it first."
    exit 1
fi

# Setup buildx builder if not already configured
echo "Setting up buildx builder..."
if ! docker buildx inspect multiarch >/dev/null 2>&1; then
    echo "Creating new buildx builder 'multiarch'..."
    docker buildx create --name multiarch --driver docker-container --use
    docker buildx inspect --bootstrap
else
    echo "Using existing buildx builder 'multiarch'..."
    docker buildx use multiarch
fi

# Install QEMU for cross-platform builds
echo ""
echo "Setting up QEMU for cross-platform emulation..."
docker run --privileged --rm tonistiigi/binfmt --install all

# Verify platforms
echo ""
echo "Available platforms:"
docker buildx inspect --bootstrap | grep Platforms

# Ask for confirmation
echo ""
echo "=============================================================================="
echo "This will build the base image for amd64 and arm64."
echo "This may take 15-20 minutes and use significant disk space."
echo "=============================================================================="
read -p "Do you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Build cancelled."
    exit 0
fi

# Build and push (or load locally if you prefer)
echo ""
echo "Building base image..."
echo ""

# Option 1: Build and push to registry (requires login)
echo "Choose build mode:"
echo "1) Push to registry (requires 'docker login ghcr.io')"
echo "2) Load locally (only builds for current platform)"
echo ""
read -p "Enter choice (1 or 2): " -n 1 -r
echo

if [[ $REPLY == "1" ]]; then
    # Push to registry
    echo ""
    echo "Checking registry login..."
    if ! docker login ghcr.io; then
        echo "❌ Please login first: docker login ghcr.io"
        exit 1
    fi

    echo ""
    echo "Building and pushing to registry..."
    docker buildx build \
        --platform ${PLATFORMS} \
        --file Dockerfile.base \
        --tag ${REPO}/${IMAGE_NAME}:latest \
        --tag ${REPO}/${IMAGE_NAME}:latest-amd64 \
        --tag ${REPO}/${IMAGE_NAME}:latest-arm64 \
        --push \
        .

    echo ""
    echo "✅ Base image built and pushed successfully!"
    echo ""
    echo "Images available at:"
    echo "  - ${REPO}/${IMAGE_NAME}:latest (multi-arch)"
    echo "  - ${REPO}/${IMAGE_NAME}:latest-amd64"
    echo "  - ${REPO}/${IMAGE_NAME}:latest-arm64"

elif [[ $REPLY == "2" ]]; then
    # Load locally (only current platform)
    CURRENT_ARCH=$(uname -m)
    if [[ "$CURRENT_ARCH" == "x86_64" ]]; then
        PLATFORM="linux/amd64"
        TAG_SUFFIX="amd64"
    elif [[ "$CURRENT_ARCH" == "aarch64" ]] || [[ "$CURRENT_ARCH" == "arm64" ]]; then
        PLATFORM="linux/arm64"
        TAG_SUFFIX="arm64"
    else
        echo "❌ Unsupported architecture: $CURRENT_ARCH"
        exit 1
    fi

    echo ""
    echo "Building for local platform: ${PLATFORM}..."
    docker buildx build \
        --platform ${PLATFORM} \
        --file Dockerfile.base \
        --tag ${REPO}/${IMAGE_NAME}:latest \
        --tag ${REPO}/${IMAGE_NAME}:latest-${TAG_SUFFIX} \
        --load \
        .

    echo ""
    echo "✅ Base image built and loaded locally!"
    echo ""
    echo "Available as:"
    echo "  - ${REPO}/${IMAGE_NAME}:latest"
    echo "  - ${REPO}/${IMAGE_NAME}:latest-${TAG_SUFFIX}"

else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo ""
echo "=============================================================================="
echo "Build completed!"
echo "=============================================================================="
