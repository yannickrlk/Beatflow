# UX/UI Improvement Plan

## 1. Business Module Fixes

### A. Dialog Validation Buttons
**Problem**: Users are confused by dialogs lacking explicit "Save" or "Validate" buttons (relying on Enter key or auto-save).
**Fix**: Add standard `Cancel` / `Save` button row to the bottom of:
- `SetMonthlyGoalDialog`
- `AddExpenseDialog`
- `AddProductDialog`

### B. Date Handling
**Problem**: "Due Date" is fixed or hard to change; Expense dates enter as text.
**Fix**:
- **Invoice Editor**: Add a `CalendarWidget` (or `tkcalendar`) trigger for the Due Date field.
- **Add Expense**: Replace the Date entry with a `DateEntry` widget or a button that opens a calendar picker. Disallow raw text entry if prone to errors.

### C. Expenses Flexibility
**Problem**: Restricted categories and lack of context.
**Fix**:
- **Categories**: Add "Other" to the dropdown list.
- **Description**: Add a new text input field `Description` (optional) to the `AddExpenseDialog` and the `transactions` database table.

### D. Dashboard Clarity
**Problem**: "Outstanding" term is unclear.
**Fix**:
- Change label to "Outstanding (Unpaid)" OR
- Add a generic `Tooltip` or `InfoLabel` next to it: *"Total value of sent invoices currently awaiting payment."*

## 2. Studio Flow Calendar Overhaul
**Problem**: Current calendar looks "rustic" (basic grid).
**Fix**:
- **Visuals**: Use `ctk` frames for day cells with proper borders/padding.
- **Styling**:
    - Header: Modern font, separate row.
    - Day Cells: Hover effects (`fg_color`), "Today" highlight (accent color ring).
    - Event Dots: Make them smaller and distinct colors.
- **Usability**: Ensure month navigation arrows are large and styled.

## 3. Implementation Checklist
- [ ] Update `AddExpenseDialog` UI (layout + signals).
- [ ] Update `AddProductDialog` UI.
- [ ] Update `SetGoalDialog` UI.
- [ ] Implement `CalendarPicker` widget (reuse across App).
- [ ] Update `InvoiceEditor` to use CalendarPicker.
- [ ] Database migration: Add `description` column to `transactions` table.
- [ ] Refactor `CalendarView` in `ui/calendar_view.py`.
