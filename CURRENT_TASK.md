# Current Task: Phase 25 - Visual Polish (UI Overhaul)

## Status
- **Phase 24 (Business)**: COMPLETE
- **Phase 24.5 (UX Polish)**: COMPLETE
- **Phase 25 (Visual Polish)**: COMPLETE

## Objectives
Make the application feel "dense" and "pro" like Ableton or VS Code, removing the "empty/cheap" feel.

## Step-by-Step Implementation Plan

### 1. Typography (`ui/theme.py`, `assets/`)
- [x] **Assets**: Create `assets/fonts/` and add Inter/JetBrainsMono TTF files placeholder.
- [x] **Font Loader**: Modify `ui/theme.py` to load fonts on startup with platform fallbacks.
- [x] **Usage**: Update `FONTS` constant to reference "Inter" and "JetBrains Mono" with fallbacks.

### 2. Density & Layout (`ui/sidebar.py`, `ui/library.py`, `ui/tree_view.py`)
- [x] **Spacing**: Reduce `SPACING` constants in `ui/theme.py` (4px grid instead of 8px).
- [x] **Lists**: Update `SampleRow` height to 64px (from 72px), compact row padding.
- [x] **Borders**: Add 1px border (`COLORS['border']`) to main frames (Sidebar, Library Index).
- [x] **Striping**: Add alternating background colors for rows (`bg_card` vs `bg_stripe`).

### 3. Micro-Interactions
- [x] **Hover**: All sample rows highlight on mouseover with `bg_hover` color.
- [x] **Sidebar Active State**: Added vertical accent bar (3px) + background color for selected tab.

## Implementation Details

### Theme Changes (`ui/theme.py`)
- Added `SIZING` constant dictionary with component sizes
- Added `bg_stripe` color for alternating row colors
- Added `border_subtle` for very subtle borders
- Reduced spacing: xs=2, sm=4, md=8, lg=12, xl=16 (compact 4px grid)
- Font loading with platform-specific fallbacks

### Sidebar Changes (`ui/sidebar.py`)
- Added 1px border around sidebar frame
- Increased accent indicator width from 2px to 3px
- Active nav button now has `bg_hover` background color
- Uses SIZING constants for consistency

### Library Tree View Changes (`ui/tree_view.py`)
- Added 1px border around tree view frame
- Imported SIZING and FONTS constants

### Sample List Changes (`ui/library.py`)
- Added `row_index` parameter for striping
- Added hover event handlers (`_on_hover_enter`, `_on_hover_leave`)
- Reduced row height to 64px (80px with folder path)
- Uses `bg_stripe` for odd rows, `bg_card` for even rows
- Row gap reduced to `SPACING['row_gap']` (1px)

## Dependencies
- No new pip packages required
- Font files (Inter, JetBrains Mono) can be added to `assets/fonts/` for better typography

## Next Steps
See `implementation_plan.md` for remaining roadmap items (Phase 20: DAW Kit Export).
