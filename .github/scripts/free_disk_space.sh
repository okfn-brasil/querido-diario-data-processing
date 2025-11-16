#!/usr/bin/env bash
# Free up disk space on GitHub Actions runners
# Based on Apache Flink's cleanup script
# GitHub Actions runners typically have:
# - Total space: ~85GB
# - Allocated: ~67GB
# - Free: ~17GB
# This script frees up ~30GB+ by removing unneeded packages

set -e

echo "=============================================================================="
echo "Freeing up disk space on CI system"
echo "=============================================================================="

echo "Disk space before cleanup:"
df -h

echo "Removing large packages..."
sudo apt-get remove -y '^ghc-8.*' '^ghc-9.*' || true
sudo apt-get remove -y '^dotnet-.*' || true
sudo apt-get remove -y '^llvm-.*' || true
sudo apt-get remove -y 'php.*' || true
sudo apt-get remove -y google-cloud-sdk hhvm google-chrome-stable firefox powershell mono-devel || true
sudo apt-get remove -y temurin-* || true
sudo apt-get autoremove -y
sudo apt-get clean

echo "Removing large directories..."
sudo rm -rf /usr/share/dotnet/ || true
sudo rm -rf /usr/local/lib/android || true
sudo rm -rf /opt/ghc || true
sudo rm -rf /opt/hostedtoolcache/CodeQL || true
sudo rm -rf /usr/local/share/boost || true
sudo rm -rf /usr/local/graalvm/ || true
sudo rm -rf /usr/local/.ghcup/ || true
sudo rm -rf /usr/local/share/powershell || true
sudo rm -rf /usr/local/share/chromium || true
sudo rm -rf /usr/local/lib/node_modules || true

echo "Removing Docker images..."
sudo docker system prune -af || true

echo "Disk space after cleanup:"
df -h

echo "Cleanup completed successfully!"
