# iOS Platform

## Overview
This directory contains iOS-specific build configurations and deployment guides.

## Prerequisites
- Xcode 14.0+
- iOS 15.0+
- CocoaPods 1.11.0+

## Getting Started
1. Install dependencies: `pod install`
2. Open `.xcworkspace` in Xcode
3. Build and run

## Building
```bash
xcodebuild -workspace YourApp.xcworkspace -scheme YourApp -configuration Release
```

## Testing
```bash
xcodebuild test -workspace YourApp.xcworkspace -scheme YourApp -destination 'platform=iOS Simulator,name=iPhone 14'
```

## Deployment
- App Store
- Enterprise/Ad Hoc
- TestFlight

## Platform Notes
- Supports iOS 15.0+
- Optimized for all iPhone models
- Dark mode support

## Troubleshooting
- Clean build folder if needed
- Verify certificates and profiles
- Check CocoaPods installation

## License
See main LICENSE file.
