# ProducerOS Business Module - Feature Specification

## Overview
The **Business Module** helps producers manage their finances, invoice clients, and track the "business" side of their career directly within ProducerOS. This transforms the app from a creative tool into a complete professional suite.

## Core Philosophy
"Simple enough for a creative, powerful enough for a pro."
Avoid complex double-entry accounting complexity. Focus on **Cash Flow** (Money In / Money Out) and **Professionalism** (Invoices).

---

## Proposed Tabs / Sections

### 1. 📊 Dashboard (Overview)
A high-level view of financial health.
*   **Revenue Cards**: Total Revenue (Month/Year), Net Profit, Expenses.
*   **Mini-Ledger**: "Recent Transactions" list (last 5 items).
*   **Goals**: A simple progress bar towards a monthly income target (e.g., "$500 / $1000").
*   **Income Sourcing**: Pie chart showing where money comes from (e.g., Beat Leases vs. Custom Beats vs. Mixing).

### 2. 🧾 Invoices (The "Killer Feature")
Generate professional PDF invoices for clients (linked to the Network module).
*   **Invoice Generator**:
    *   Select Client (from Network).
    *   Add Items (Manually or from Product Catalog).
    *   Set Due Date & Tax Rate (VAT/Sales Tax).
    *   Terms & Notes section (e.g., "50% deposit required").
*   **Status Tracking**:
    *   `Draft` (Gray): Work in progress.
    *   `Sent` (Blue): Waiting for payment.
    *   `Paid` (Green): Money received (auto-adds to Revenue).
    *   `Overdue` (Red): Past due date.
*   **PDF Export**: One-click generation of a branded PDF (using ReportLab) to email to clients.

### 3. 💰 Ledger (Income & Expenses)
manual tracking of every dollar.
*   **Income Log**:
    *   Beat Sales (BeatStars, Airbit, Email).
    *   Services (Mixing, Mastering).
    *   Royalties (DistroKid, ASCAP).
*   **Expense Log**:
    *   **Studio Gear**: Hardware, cables, interfaces.
    *   **Software**: Plugins, VSTs, DAW upgrades.
    *   **Subscriptions**: Splice, Spotify, Adobe, DistroKid.
    *   **Marketing**: FB Ads, Promo, Website hosting.
*   **Features**:
    *   Filter by Date Range.
    *   Filter by Category.
    *   Export to CSV (for sending to an accountant).

### 4. 🏷️ Product & Service Catalog (Price List)
Save time by defining standard prices.
*   **Products (Beat Licenses)**:
    *   "MP3 Lease" - $29.99
    *   "WAV Lease" - $49.99
    *   "Trackout/Stems" - $99.99
    *   "Exclusive Rights" - $500.00
*   **Services**:
    *   "Mixing (2 Track)" - $50.00
    *   "Full Mix & Master" - $150.00
    *   "Custom Beat Production" - $300.00
*   **Usage**: These presets appear in dropdowns when creating Invoices or logging Income.

---

## Technical Implementation Plan

### Database Schema Changes
New tables in `produceros.db`:
*   `products`: `id, title, type (license/service), price, description`
*   `transactions`: `id, type (income/expense), amount, category, date, description, linked_invoice_id`
*   `invoices`: `id, client_id, status, due_date, created_date, subtotal, tax, total, notes`
*   `invoice_items`: `id, invoice_id, description, quantity, unit_price, total`

### Python Dependencies
*   `reportlab`: For generating robust PDF invoices.
*   `matplotlib`: (Already included) For the charts.

### UI Architecture
*   `ui/business_view.py`: Main container.
*   `ui/business_dashboard.py`: Statistics and charts.
*   `ui/invoice_editor.py`: The complex form for creating invoices.
*   `ui/ledger_view.py`: Table view of transactions.

## User Flow Example
1.  User finishes a beat for a client.
2.  Goes to **Business > Invoices**.
3.  Clicks "New Invoice", selects Client "Rapper X".
4.  Adds item "Custom Beat Production" ($300) from Catalog.
5.  Clicks "Generate PDF". Invoice is saved to `ProducerOS/Invoices/`.
6.  Sends PDF to client.
7.  When client pays, user marks Invoice as "Paid".
8.  $300 is automatically added to the **Ledger** as Income.
9.  **Dashboard** updates to show progress towards monthly goal.
