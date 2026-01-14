# Font Assets for ProducerOS

This directory should contain the following font files for the professional UI:

## Required Fonts

### Inter (Primary UI Font)
- `Inter-Regular.ttf`
- `Inter-Medium.ttf`
- `Inter-Bold.ttf`

Download from: https://github.com/rsms/inter/releases

### JetBrains Mono (Monospace for Data)
- `JetBrainsMono-Regular.ttf`
- `JetBrainsMono-Medium.ttf`

Download from: https://github.com/JetBrains/JetBrainsMono/releases

## Installation

1. Download the fonts from the links above
2. Copy the .ttf files to this directory
3. Restart ProducerOS

## Fallback Behavior

If fonts are not present, the application will use system fallback fonts:
- Inter -> Segoe UI (Windows) / SF Pro (macOS) / Cantarell (Linux)
- JetBrains Mono -> Consolas (Windows) / SF Mono (macOS) / monospace (Linux)
