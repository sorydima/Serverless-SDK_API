# macOS Platform

## Overview
This directory contains macOS-specific build configurations and deployment guides.

## Prerequisites
- Xcode 14.0+
- macOS 12.0+
- Homebrew (for dependencies)

## Getting Started
1. Install dependencies: `brew bundle`
2. Open `.xcworkspace` in Xcode
3. Build and run

## Building
```bash
xcodebuild -workspace YourApp.xcworkspace -scheme YourApp -configuration Release
```

## Testing
```bash
xcodebuild test -workspace YourApp.xcworkspace -scheme YourApp
```

## Deployment
- Mac App Store
- Direct Download
- Enterprise Distribution

## Platform Notes
- Supports Apple Silicon (arm64) and Intel (x86_64)
- Optimized for macOS 12.0+
- Dark mode support
- Menu bar and dock integration

## Troubleshooting
- Clean build folder if needed
- Verify code signing
- Check system requirements

## License
See main LICENSE file.
