# Implementation Plan: Clients Manager

> [!IMPORTANT]
> This is a standalone module separate from the Sample Browser. It focuses on CRM (Customer Relationship Management) for music producers.

## Overview
The Client Manager allows producers to track their network, contact info, and social links within Beatflow.

---

## Phase 1: Foundation & Data - COMPLETE
**Goal**: Setup the persistent storage and core logic.

### Implementation (2026-01-08)
- [x] **Database Update (`core/database.py`)**:
  - Created `clients` table with all fields
  - Added index on `name` for fast searches
- [x] **Client Manager Core (`core/client_manager.py`)**:
  - CRUD operations: `add_client`, `get_clients`, `get_client`, `update_client`, `delete_client`
  - `get_client_count()` for stats
  - `open_social_link(platform, handle)` - opens Instagram/Twitter/website in browser
  - Singleton pattern with `get_client_manager()`

---

## Phase 2: Navigation & View Switching - COMPLETE
**Goal**: Integrate the "Clients" tab into the main app.

### Implementation (2026-01-08)
- [x] **Sidebar (`ui/sidebar.py`)**:
  - Added "Clients" navigation button with icon `\U0001f464`
  - Navigation items now include: Browse, Clients
- [x] **View Switcher (`ui/app.py`)**:
  - `_on_nav_change()` handles switching between views
  - `_show_browse_view()` / `_show_clients_view()` methods
  - Uses `grid_remove()` to preserve state when switching
  - Sample browser search/scroll state preserved when viewing clients

---

## Phase 3: The Clients View (UI) - COMPLETE
**Goal**: Create a premium interactive interface for client management.

### Implementation (2026-01-08)
- [x] **View Container (`ui/clients_view.py`)**:
  - Top Bar: Search, "Add Client" button, View Toggle (Card/List)
  - Header matches Browse view (height=56, width=160 toggle, dynamic_resizing=False)
  - Responsive grid layout for Card view (CARD_MIN_WIDTH=280)
  - Table layout with headers for List view
  - Search filters clients by name in real-time
  - Empty state with friendly message
  - Client count label in topbar
- [x] **Client Card Component (`ui/client_card.py`)**:
  - `ClientCard`: Premium glass card with name, contact info, social buttons
  - `ClientListRow`: Compact table row with same data
  - Hover effects (accent border on cards, bg highlight on rows)
  - Edit button (pencil icon ✎) on each card/row
- [x] **Client Dialogs (`ui/client_dialogs.py`)**:
  - `AddClientDialog` (450x500): Scrollable form, name validation
  - `EditClientDialog` (450x520): Pre-populated fields, delete option
  - Buttons always visible at bottom (outside scroll area)
- [x] **Social Icons (Unicode)**:
  - Instagram: ◎ `\u25CE` (bullseye/lens, hover=#E1306C)
  - Twitter/X: ╳ `\u2573` (box X, hover=#000000)
  - Website: ↗ `\u2197` (external link arrow)

---

## Phase 4: Polish & Settings - PENDING
**Goal**: Final refinements and settings persistence.

- [ ] **Settings Integration**:
  - Persist "Default View" (Card or List) in `beatflow_config.json`
- [ ] **Delete Confirmation**:
  - Add confirmation dialog before deleting a client
- [ ] **Keyboard Shortcuts**:
  - Enter to save in dialogs
  - Escape to cancel
- [ ] **Visual Polish**:
  - Refinements based on user feedback
