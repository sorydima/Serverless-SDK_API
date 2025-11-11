# Windows UWP Platform

## Overview
This directory contains Universal Windows Platform (UWP) specific configurations and deployment guides.

## Prerequisites
- Windows 10/11 SDK (10.0.19041.0 or later)
- Visual Studio 2022 with UWP development workload
- Windows 10/11 (for development and testing)

## Getting Started
1. Open the solution in Visual Studio 2022
2. Select x64 or ARM64 as the target platform
3. Build and deploy to local machine

## Building
1. From Visual Studio:
   - Select Release/x64 or Release/ARM64
   - Build > Build Solution (Ctrl+Shift+B)

2. From command line:
   ```powershell
   msbuild YourApp.sln /p:Configuration=Release /p:Platform=x64
   ```

## Testing
1. Run unit tests from Test Explorer in Visual Studio
2. For UI tests, use WinAppDriver

## Packaging
1. Right-click on the project > Store > Create App Packages
2. Follow the packaging wizard
3. Choose between:
   - Sideloading
   - Microsoft Store submission
   - Enterprise distribution

## Platform Notes
- Target OS version: Windows 10 (10.0.19041.0) or later
- Supports both x64 and ARM64 architectures
- Sandboxed execution environment
- Limited Win32 API surface

## Capabilities
- File system access (with user consent)
- Network capabilities
- Bluetooth (if required)
- Webcam/microphone (if required)

## Troubleshooting
- Check package.appxmanifest for required capabilities
- Verify target platform version
- Check Windows Developer Mode is enabled
- Review Event Viewer for runtime errors

## Deployment
- Microsoft Store
- Business Store
- Sideloading for enterprises
- MDM deployment

## License
See main LICENSE file.
