# Linux Platform

## Overview
This directory contains Linux-specific build configurations and deployment guides.

## Prerequisites
- GCC 11+ or Clang 13+
- CMake 3.24+
- pkg-config
- System dependencies (install via package manager)

## Getting Started
### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake pkg-config
```

### Fedora/RHEL
```bash
sudo dnf groupinstall "Development Tools"
sudo dnf install cmake pkg-config
```

## Building
```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

## Installation
```bash
sudo make install
```

## Packaging
### DEB (Debian/Ubuntu)
```bash
cpack -G DEB
```

### RPM (Fedora/RHEL)
```bash
cpack -G RPM
```

## Platform Notes
- Supports major distributions (Ubuntu, Debian, Fedora, RHEL, etc.)
- Systemd service files included
- AppImage support available
- Flatpak/Snap packages (see packaging/)

## Troubleshooting
- Check missing dependencies with `ldd`
- Verify library paths
- Check system logs for runtime issues

## License
See main LICENSE file.
