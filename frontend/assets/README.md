# Assets

This directory contains static assets for the AssetFlow Flutter application.

## Structure

```
assets/
├── images/          # Image assets (PNG, JPG, SVG)
├── icons/           # Icon assets
└── README.md        # This file
```

## Usage

Assets are referenced in `pubspec.yaml` and can be used in the app like:

```dart
// Images
Image.asset('assets/images/logo.png')

// Icons
Image.asset('assets/icons/wallet.svg')
```

## Guidelines

- Use SVG for icons when possible for better scalability
- Optimize images for mobile (compress and resize appropriately)
- Use descriptive filenames
- Group related assets in subdirectories