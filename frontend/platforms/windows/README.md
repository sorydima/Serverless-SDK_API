# Windows Platform

## Overview
This directory contains Windows-specific build configurations and deployment guides.

## Prerequisites
- Visual Studio 2022 (with C++ and .NET workloads)
- Windows 10/11 SDK
- CMake 3.24+
- vcpkg (for dependencies)

## Getting Started
1. Install dependencies:
   ```powershell
   vcpkg install --triplet x64-windows
   ```
2. Generate build files:
   ```powershell
   cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=[vcpkg-root]/scripts/buildsystems/vcpkg.cmake
   ```
3. Build the solution

## Building
```powershell
cmake --build build --config Release
```

## Testing
```powershell
ctest --test-dir build --output-on-failure
```

## Deployment
- MSIX Package
- Sideloading
- Enterprise Deployment

## Platform Notes
- Supports Windows 10/11 (x64, ARM64)
- MSIX packaging for modern deployment
- Desktop Bridge compatible
- High DPI support

## Troubleshooting
- Check Windows SDK installation
- Verify Visual Studio build tools
- Ensure proper environment variables

## License
See main LICENSE file.
