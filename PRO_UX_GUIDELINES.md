# Technical Design Specification: Professional UI Upgrade

This document provides Claude with the exact technical requirements to implement the "Cyber-Premium" design system for Beatflow.

---

## 1. Global Color System (`ui/theme.py`)

Update the `COLORS` dictionary with these specific hex codes. Do not use generic names; follow this palette:

| Key | Hex Code | Usage |
| :--- | :--- | :--- |
| `bg_darkest` | `#0D0D11` | Sidebar background. |
| `bg_dark` | `#121217` | Library Index (Tree view). |
| `bg_main` | `#18181E` | Main Sample List background. |
| `bg_card` | `#1E1E26` | Sample Row default state. |
| `bg_hover` | `#262632` | Hover effects on all interactive elements. |
| `accent` | `#FF6100` | Primary buttons, play icons, focus states. |
| `accent_secondary`| `#8B5CF6` | Detected metadata (BPM/Key), Analysis buttons. |
| `fg` | `#FFFFFF` | Primary text. |
| `fg_secondary` | `#A0A0B0` | Muted descriptions (BPM/Key labels). |
| `fg_dim` | `#606070` | Secondary metadata (Bitrate, Format, Path). |
| `border` | `#2D2D3A` | Subtle dividers between rows/sections. |

---

## 2. Component Enhancements

### A. The "Professional" Sidebar (`ui/sidebar.py`)
- **Spacing**: Increase `pady` between nav items to `4px` to allow for better breathing room.
- **Micro-interaction**: On hover, the text color should shift from `fg_secondary` to `fg` instantly.
- **Active State**: Use a `2px` wide vertical bar of `accent` color on the far left of the button to indicate the active section.

### B. High-Fidelity Sample Rows (`ui/library.py`)
- **Visual Hierarchy**: 
  - The filename should be **Bold** and `14pt`.
  - BPM and Key should use a monospaced font if possible (`JetBrains Mono` or `Consolas`).
- **State Feedback**:
  - **Playing State**: The row background should shift to `#22222C` with a subtle `1px` border of `accent` color.
  - **Waveform Colors**: Use `accent` for the foreground and `bg_hover` for the background of the waveform image.
- **Spacing**: Add `12px` of horizontal padding inside the `SampleRow` container.

### C. Tree View Polish (`ui/tree_view.py`)
- **Icons**: Replace text arrows (`\u25b6`) with the appropriate modern SVG or thinner characters if supported.
- **Indentation**: Use a strict `16px` indentation per level for a cleaner hierarchy.

---

## 3. Global UX Requirements

### 1. Spacing & Grids (The "8px" Rule)
All margins and paddings must be multiples of 8 (`8px`, `16px`, `24px`, `32px`). This ensures a mathematically consistent "pro" layout.

### 2. Loading State (Skeleton Feel)
When a waveform is loading, the row should show a greyed-out rectangle with a `2px` rounded corner, not just a text label.

### 3. Typography
If the OS supports it, force `Inter` as the primary font. Fallback: `Segoe UI` (Windows) or `San Francisco` (macOS).

---

## 4. Implementation Checklist for Claude

- [ ] Update `ui/theme.py` with the new color palette.
- [ ] Refactor `SampleRow` in `ui/library.py` to use the new "Playing State" visual indicators.
- [ ] Adjust all `padx`/`pady` in `ui/app.py`, `ui/sidebar.py`, and `ui/library.py` to follow the 8px grid rule.
- [ ] Update `ui/tree_view.py` with cleaner indentation and modern separators.
- [ ] Implement the "Glow" effect or highlight for the currently playing track.
