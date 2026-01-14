"""Ledger View for ProducerOS - Income and expense tracking."""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
from ui.theme import COLORS, SPACING
from core.business import get_business_manager, INCOME_CATEGORIES, EXPENSE_CATEGORIES
from ui.date_picker import DatePickerWidget


class LedgerView(ctk.CTkFrame):
    """View for tracking income and expenses."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.business = get_business_manager()
        self.transaction_widgets = []

        self._build_ui()

    def _build_ui(self):
        """Build the ledger view UI."""
        # Header with filters and buttons
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING['md']))

        # Type filter
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="left")

        type_label = ctk.CTkLabel(
            filter_frame,
            text="Type:",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        )
        type_label.pack(side="left", padx=(0, SPACING['xs']))

        self.type_var = ctk.StringVar(value="All")
        self.type_filter = ctk.CTkSegmentedButton(
            filter_frame,
            values=["All", "Income", "Expense"],
            variable=self.type_var,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=180,
            height=32,
            corner_radius=4,
            command=self._on_filter_change
        )
        self.type_filter.pack(side="left")

        # Category filter
        cat_label = ctk.CTkLabel(
            filter_frame,
            text="Category:",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        )
        cat_label.pack(side="left", padx=(SPACING['md'], SPACING['xs']))

        self.category_var = ctk.StringVar(value="All")
        all_categories = ["All"] + INCOME_CATEGORIES + EXPENSE_CATEGORIES
        self.category_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.category_var,
            values=all_categories,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_card'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            width=130,
            height=32,
            corner_radius=4,
            command=self._on_filter_change
        )
        self.category_filter.pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        # Export CSV button
        export_btn = ctk.CTkButton(
            btn_frame,
            text="Export CSV",
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            height=32,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self._on_export_csv
        )
        export_btn.pack(side="left", padx=SPACING['xs'])

        # Add expense button
        expense_btn = ctk.CTkButton(
            btn_frame,
            text="+ Expense",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#EF4444",
            hover_color="#DC2626",
            height=36,
            corner_radius=4,
            text_color="#ffffff",
            command=lambda: self._on_add_transaction("expense")
        )
        expense_btn.pack(side="left", padx=SPACING['xs'])

        # Add income button
        income_btn = ctk.CTkButton(
            btn_frame,
            text="+ Income",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#22C55E",
            hover_color="#16A34A",
            height=36,
            corner_radius=4,
            text_color="#ffffff",
            command=lambda: self._on_add_transaction("income")
        )
        income_btn.pack(side="left")

        # Summary bar
        self.summary_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=4, height=50)
        self.summary_frame.pack(fill="x", pady=(0, SPACING['md']))
        self.summary_frame.pack_propagate(False)

        # Summary labels
        self.income_total = ctk.CTkLabel(
            self.summary_frame,
            text="Income: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color="#22C55E"
        )
        self.income_total.pack(side="left", padx=SPACING['lg'])

        self.expense_total = ctk.CTkLabel(
            self.summary_frame,
            text="Expenses: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color="#EF4444"
        )
        self.expense_total.pack(side="left", padx=SPACING['lg'])

        self.net_total = ctk.CTkLabel(
            self.summary_frame,
            text="Net: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        self.net_total.pack(side="left", padx=SPACING['lg'])

        # Transaction list
        self.list_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.list_scroll.pack(fill="both", expand=True)

        # List header
        list_header = ctk.CTkFrame(self.list_scroll, fg_color=COLORS['bg_dark'], height=36, corner_radius=4)
        list_header.pack(fill="x", pady=(0, SPACING['xs']))
        list_header.pack_propagate(False)

        headers = [
            ("Date", 90),
            ("Type", 70),
            ("Category", 120),
            ("Description", 250),
            ("Amount", 100),
            ("Actions", 60)
        ]

        for label, width in headers:
            lbl = ctk.CTkLabel(
                list_header,
                text=label,
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=COLORS['fg_secondary'],
                width=width,
                anchor="w" if label != "Amount" else "e"
            )
            lbl.pack(side="left", padx=SPACING['xs'])

        # Transaction rows container
        self.rows_container = ctk.CTkFrame(self.list_scroll, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.list_scroll, fg_color="transparent")

        empty_icon = ctk.CTkLabel(
            self.empty_frame,
            text="\U0001f4b0",  # Money bag emoji
            font=ctk.CTkFont(size=48),
            text_color=COLORS['fg_dim']
        )
        empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

        empty_msg = ctk.CTkLabel(
            self.empty_frame,
            text="No Transactions Yet",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        empty_msg.pack()

        empty_submsg = ctk.CTkLabel(
            self.empty_frame,
            text="Start tracking your income and expenses\nto see your financial health.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary'],
            justify="center"
        )
        empty_submsg.pack(pady=(SPACING['sm'], SPACING['lg']))

    def refresh(self):
        """Refresh transaction list."""
        # Clear existing
        for widget in self.transaction_widgets:
            widget.destroy()
        self.transaction_widgets = []

        # Get filters
        type_filter = self.type_var.get().lower()
        if type_filter == "all":
            type_filter = None

        category_filter = self.category_var.get()
        if category_filter == "All":
            category_filter = None

        transactions = self.business.get_transactions(
            type=type_filter,
            category=category_filter
        )

        # Calculate totals
        income_sum = sum(t['amount'] for t in transactions if t['type'] == 'income')
        expense_sum = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        net = income_sum - expense_sum

        self.income_total.configure(text=f"Income: ${income_sum:,.2f}")
        self.expense_total.configure(text=f"Expenses: ${expense_sum:,.2f}")
        self.net_total.configure(
            text=f"Net: ${net:,.2f}",
            text_color="#22C55E" if net >= 0 else "#EF4444"
        )

        if not transactions:
            self.rows_container.pack_forget()
            self.empty_frame.pack(expand=True)
            return

        self.empty_frame.pack_forget()
        self.rows_container.pack(fill="both", expand=True)

        for txn in transactions:
            row = self._create_transaction_row(txn)
            row.pack(fill="x", pady=2)
            self.transaction_widgets.append(row)

    def _create_transaction_row(self, txn: dict) -> ctk.CTkFrame:
        """Create a row for a transaction."""
        is_income = txn.get('type') == 'income'

        row = ctk.CTkFrame(
            self.rows_container,
            fg_color=COLORS['bg_card'],
            corner_radius=4,
            height=44
        )
        row.pack_propagate(False)

        # Date
        date_lbl = ctk.CTkLabel(
            row,
            text=txn.get('date', ''),
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            width=90,
            anchor="w"
        )
        date_lbl.pack(side="left", padx=SPACING['xs'])

        # Type badge
        type_badge = ctk.CTkLabel(
            row,
            text="Income" if is_income else "Expense",
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color="#22C55E" if is_income else "#EF4444",
            fg_color=COLORS['bg_dark'],
            corner_radius=4,
            width=60,
            height=22
        )
        type_badge.pack(side="left", padx=SPACING['xs'])

        # Category
        cat_lbl = ctk.CTkLabel(
            row,
            text=txn.get('category', 'N/A')[:15],
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            width=120,
            anchor="w"
        )
        cat_lbl.pack(side="left", padx=SPACING['xs'])

        # Description
        desc_lbl = ctk.CTkLabel(
            row,
            text=txn.get('description', '')[:35],
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg'],
            width=250,
            anchor="w"
        )
        desc_lbl.pack(side="left", padx=SPACING['xs'])

        # Amount
        amount_text = f"+${txn.get('amount', 0):,.2f}" if is_income else f"-${txn.get('amount', 0):,.2f}"
        amount_lbl = ctk.CTkLabel(
            row,
            text=amount_text,
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            text_color="#22C55E" if is_income else "#EF4444",
            width=100,
            anchor="e"
        )
        amount_lbl.pack(side="left", padx=SPACING['xs'])

        # Actions
        actions = ctk.CTkFrame(row, fg_color="transparent", width=60)
        actions.pack(side="right", padx=SPACING['xs'])
        actions.pack_propagate(False)

        # Edit button
        edit_btn = ctk.CTkButton(
            actions,
            text="\u270E",  # Edit icon
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=28,
            height=28,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=lambda t=txn: self._on_edit_transaction(t)
        )
        edit_btn.pack(side="left")

        # Delete button
        del_btn = ctk.CTkButton(
            actions,
            text="\u2715",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#EF4444",
            width=28,
            height=28,
            corner_radius=4,
            text_color=COLORS['fg_dim'],
            command=lambda t=txn: self._on_delete_transaction(t)
        )
        del_btn.pack(side="left")

        return row

    def _on_filter_change(self, value=None):
        """Handle filter change."""
        self.refresh()

    def _on_add_transaction(self, txn_type: str):
        """Add a new transaction."""
        dialog = TransactionDialog(self.winfo_toplevel(), self.business, txn_type=txn_type)
        self.wait_window(dialog)
        self.refresh()

    def _on_edit_transaction(self, txn: dict):
        """Edit a transaction."""
        dialog = TransactionDialog(self.winfo_toplevel(), self.business, transaction=txn)
        self.wait_window(dialog)
        self.refresh()

    def _on_delete_transaction(self, txn: dict):
        """Delete a transaction."""
        if messagebox.askyesno(
            "Delete Transaction",
            f"Delete this {txn.get('type')} of ${txn.get('amount', 0):.2f}?",
            parent=self.winfo_toplevel()
        ):
            self.business.delete_transaction(txn['id'])
            self.refresh()

    def _on_export_csv(self):
        """Export transactions to CSV."""
        filepath = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Export Transactions as CSV",
            initialfile=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not filepath:
            return

        # Get all transactions
        transactions = self.business.get_transactions()

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write("Date,Type,Category,Description,Amount\n")

                # Data
                for txn in transactions:
                    date = txn.get('date', '')
                    txn_type = txn.get('type', '')
                    category = txn.get('category', '')
                    desc = txn.get('description', '').replace(',', ';')
                    amount = txn.get('amount', 0)

                    # Negative for expenses
                    if txn_type == 'expense':
                        amount = -amount

                    f.write(f"{date},{txn_type},{category},{desc},{amount:.2f}\n")

            messagebox.showinfo(
                "Export Complete",
                f"Exported {len(transactions)} transactions to:\n{filepath}",
                parent=self.winfo_toplevel()
            )
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Failed to export: {str(e)}",
                parent=self.winfo_toplevel()
            )


class TransactionDialog(ctk.CTkToplevel):
    """Dialog for creating/editing transactions."""

    def __init__(self, parent, business, txn_type: str = "income", transaction: dict = None):
        super().__init__(parent)

        self.business = business
        self.txn_type = txn_type if not transaction else transaction.get('type', 'income')
        self.transaction = transaction
        self.is_edit = transaction is not None

        self.title("Edit Transaction" if self.is_edit else f"Add {self.txn_type.title()}")
        self.geometry("420x420")
        self.minsize(380, 350)
        self.resizable(True, True)

        self.configure(fg_color=COLORS['bg_main'])
        self.transient(parent)
        self.grab_set()

        self._build_ui()

        if self.is_edit:
            self._load_transaction()

    def _build_ui(self):
        """Build dialog UI with scrollable content."""
        # Grid layout for main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS['bg_card'], corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # Type indicator
        type_color = "#22C55E" if self.txn_type == "income" else "#EF4444"
        ctk.CTkLabel(
            scroll, text=f"{self.txn_type.upper()}",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=type_color
        ).pack(anchor="w", padx=16, pady=(16, 12))

        # Amount
        ctk.CTkLabel(
            scroll, text="Amount *",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=16, pady=(0, 4))

        amount_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        amount_frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            amount_frame, text="$",
            font=ctk.CTkFont(family="JetBrains Mono", size=16),
            text_color=COLORS['fg']
        ).pack(side="left")

        self.amount_entry = ctk.CTkEntry(
            amount_frame, font=ctk.CTkFont(family="JetBrains Mono", size=16),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=40, placeholder_text="0.00"
        )
        self.amount_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Category
        ctk.CTkLabel(
            scroll, text="Category",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=16, pady=(0, 4))

        categories = INCOME_CATEGORIES if self.txn_type == "income" else EXPENSE_CATEGORIES
        self.category_var = ctk.StringVar(value=categories[0])
        self.category_dropdown = ctk.CTkOptionMenu(
            scroll, variable=self.category_var, values=categories,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_input'], button_color=COLORS['bg_hover'],
            dropdown_fg_color=COLORS['bg_card'],
            height=36, corner_radius=4, width=200
        )
        self.category_dropdown.pack(anchor="w", padx=16, pady=(0, 12))

        # Date
        ctk.CTkLabel(
            scroll, text="Date",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=16, pady=(0, 4))

        date_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        date_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.date_picker = DatePickerWidget(
            date_frame, initial_date=datetime.now().strftime('%Y-%m-%d')
        )
        self.date_picker.pack(anchor="w")

        # Description
        ctk.CTkLabel(
            scroll, text="Description (optional)",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self.desc_entry = ctk.CTkEntry(
            scroll, font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=36, placeholder_text="What was this for?"
        )
        self.desc_entry.pack(fill="x", padx=16, pady=(0, 16))

        # Buttons (fixed at bottom)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

        ctk.CTkButton(
            btn_frame, text="Cancel",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'], hover_color=COLORS['bg_dark'],
            height=36, width=90, corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        save_color = "#22C55E" if self.txn_type == "income" else "#EF4444"
        save_hover = "#16A34A" if self.txn_type == "income" else "#DC2626"
        ctk.CTkButton(
            btn_frame, text="Save",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=save_color, hover_color=save_hover,
            height=36, width=100, corner_radius=4,
            text_color="#ffffff",
            command=self._on_save
        ).pack(side="right")

    def _load_transaction(self):
        """Load existing transaction data."""
        if not self.transaction:
            return

        self.amount_entry.insert(0, f"{self.transaction.get('amount', 0):.2f}")
        self.category_var.set(self.transaction.get('category', ''))

        date = self.transaction.get('date', '')
        if date:
            self.date_picker.set_date(date)

        desc = self.transaction.get('description', '')
        if desc:
            self.desc_entry.insert(0, desc)

    def _on_save(self):
        """Save transaction."""
        try:
            amount = float(self.amount_entry.get().replace(',', ''))
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.", parent=self)
            return

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than 0.", parent=self)
            return

        data = {
            'type': self.txn_type,
            'amount': amount,
            'category': self.category_var.get(),
            'date': self.date_picker.get_date(),
            'description': self.desc_entry.get().strip()
        }

        if self.is_edit:
            self.business.update_transaction(self.transaction['id'], data)
        else:
            self.business.add_transaction(data)

        self.destroy()
