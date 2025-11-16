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

echo ""
echo "=============================================================================="
echo "Analyzing large packages and directories (for future optimization)..."
echo "=============================================================================="

# List top 20 largest packages
echo ""
echo "Top 20 largest packages:"
dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -rn | head -n 20 | awk '{printf "  %6.1f MB  %s\n", $1/1024, $2}'

# Find large directories in common locations
echo ""
echo "Large directories (>500MB) in /usr:"
du -h -d 2 /usr/ 2>/dev/null | grep -E "^[0-9.]+G|^[5-9][0-9][0-9]M" | sort -rh | head -n 15 || true

echo ""
echo "Large directories (>500MB) in /opt:"
du -h -d 2 /opt/ 2>/dev/null | grep -E "^[0-9.]+G|^[5-9][0-9][0-9]M" | sort -rh | head -n 10 || true

echo ""
echo "Large directories (>500MB) in /usr/local:"
du -h -d 2 /usr/local/ 2>/dev/null | grep -E "^[0-9.]+G|^[5-9][0-9][0-9]M" | sort -rh | head -n 10 || true

echo ""
echo "=============================================================================="
echo "Starting cleanup..."
echo "=============================================================================="

echo ""
echo "Removing large packages..."
sudo apt-get remove -y '^ghc-8.*' '^ghc-9.*' || true
sudo apt-get remove -y '^dotnet-.*' || true
sudo apt-get remove -y '^llvm-.*' || true
sudo apt-get remove -y 'php.*' || true
sudo apt-get remove -y azure-cli google-cloud-sdk hhvm google-chrome-stable firefox powershell mono-devel || true
sudo apt-get remove -y temurin-* || true
sudo apt-get remove -y '^mysql-.*' || true
sudo apt-get remove -y '^mongodb-.*' || true
sudo apt-get remove -y '^postgresql-.*' || true
sudo apt-get remove -y snapd || true
sudo apt-get autoremove -y
sudo apt-get clean

echo ""
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
sudo rm -rf /usr/share/swift || true
sudo rm -rf /usr/local/julia* || true
sudo rm -rf /usr/share/kotlinc || true
sudo rm -rf /usr/local/aws-cli || true
sudo rm -rf /root/.rustup || true
sudo rm -rf /root/.cargo || true
sudo rm -rf /imagegeneration || true

echo ""
echo "Removing Docker images and build cache..."
sudo docker system prune -af --volumes || true
sudo rm -rf /var/lib/docker/tmp/* || true

echo ""
echo "Removing APT cache..."
sudo rm -rf /var/cache/apt/archives/* || true
sudo rm -rf /var/lib/apt/lists/* || true

echo ""
echo "Removing snap cache..."
sudo rm -rf /var/lib/snapd/cache/* || true

echo ""
echo "=============================================================================="
echo "Cleanup completed!"
echo "=============================================================================="

echo ""
echo "Disk space after cleanup:"
df -h

echo ""
echo "Summary of freed space:"
df -h / | awk 'NR==1 {print "  " $0} NR==2 {print "  " $0 " (root filesystem)"}'
