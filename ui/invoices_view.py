"""Invoices View for ProducerOS - Invoice list and editor."""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta
from ui.theme import COLORS, SPACING
from core.business import get_business_manager, INVOICE_STATUSES
from core.client_manager import get_client_manager
from ui.date_picker import DatePickerWidget


class InvoicesView(ctk.CTkFrame):
    """View for managing invoices."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.business = get_business_manager()
        self.client_manager = get_client_manager()
        self.invoice_widgets = []

        self._build_ui()

    def _build_ui(self):
        """Build the invoices view UI."""
        # Header with filters and new invoice button
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING['md']))

        # Status filter
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="left")

        filter_label = ctk.CTkLabel(
            filter_frame,
            text="Status:",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        )
        filter_label.pack(side="left", padx=(0, SPACING['xs']))

        self.status_var = ctk.StringVar(value="All")
        status_options = ["All"] + [s['label'] for s in INVOICE_STATUSES.values()]
        self.status_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.status_var,
            values=status_options,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_card'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            width=100,
            height=32,
            corner_radius=4,
            command=self._on_filter_change
        )
        self.status_filter.pack(side="left")

        # New Invoice button
        new_btn = ctk.CTkButton(
            header,
            text="+ New Invoice",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=36,
            corner_radius=4,
            text_color="#ffffff",
            command=self._on_new_invoice
        )
        new_btn.pack(side="right")

        # Invoice list
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
            ("Invoice #", 100),
            ("Client", 150),
            ("Date", 90),
            ("Due", 90),
            ("Status", 80),
            ("Total", 100),
            ("Actions", 120)
        ]

        for label, width in headers:
            lbl = ctk.CTkLabel(
                list_header,
                text=label,
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=COLORS['fg_secondary'],
                width=width,
                anchor="w" if label != "Total" else "e"
            )
            lbl.pack(side="left", padx=SPACING['xs'])

        # Invoice rows container
        self.rows_container = ctk.CTkFrame(self.list_scroll, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.list_scroll, fg_color="transparent")

        empty_icon = ctk.CTkLabel(
            self.empty_frame,
            text="\U0001f9fe",  # Receipt emoji
            font=ctk.CTkFont(size=48),
            text_color=COLORS['fg_dim']
        )
        empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

        empty_msg = ctk.CTkLabel(
            self.empty_frame,
            text="No Invoices Yet",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        empty_msg.pack()

        empty_submsg = ctk.CTkLabel(
            self.empty_frame,
            text="Create your first invoice to start\ntracking your income professionally.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary'],
            justify="center"
        )
        empty_submsg.pack(pady=(SPACING['sm'], SPACING['lg']))

        empty_btn = ctk.CTkButton(
            self.empty_frame,
            text="+ Create Invoice",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=44,
            width=160,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_new_invoice
        )
        empty_btn.pack()

    def refresh(self):
        """Refresh invoice list."""
        # Clear existing
        for widget in self.invoice_widgets:
            widget.destroy()
        self.invoice_widgets = []

        # Get status filter
        status_label = self.status_var.get()
        status = None
        if status_label != "All":
            for key, info in INVOICE_STATUSES.items():
                if info['label'] == status_label:
                    status = key
                    break

        invoices = self.business.get_invoices(status=status)

        if not invoices:
            self.rows_container.pack_forget()
            self.empty_frame.pack(expand=True)
            return

        self.empty_frame.pack_forget()
        self.rows_container.pack(fill="both", expand=True)

        for inv in invoices:
            row = self._create_invoice_row(inv)
            row.pack(fill="x", pady=2)
            self.invoice_widgets.append(row)

    def _create_invoice_row(self, invoice: dict) -> ctk.CTkFrame:
        """Create a row for an invoice."""
        row = ctk.CTkFrame(
            self.rows_container,
            fg_color=COLORS['bg_card'],
            corner_radius=4,
            height=44
        )
        row.pack_propagate(False)

        # Invoice number
        inv_num = ctk.CTkLabel(
            row,
            text=invoice.get('invoice_number', 'N/A'),
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=COLORS['accent'],
            width=100,
            anchor="w"
        )
        inv_num.pack(side="left", padx=SPACING['xs'])

        # Client
        client = ctk.CTkLabel(
            row,
            text=invoice.get('client_name', 'N/A')[:18],
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg'],
            width=150,
            anchor="w"
        )
        client.pack(side="left", padx=SPACING['xs'])

        # Date
        date = ctk.CTkLabel(
            row,
            text=invoice.get('created_date', ''),
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            width=90,
            anchor="w"
        )
        date.pack(side="left", padx=SPACING['xs'])

        # Due date
        due = ctk.CTkLabel(
            row,
            text=invoice.get('due_date', 'N/A'),
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            width=90,
            anchor="w"
        )
        due.pack(side="left", padx=SPACING['xs'])

        # Status badge
        status = invoice.get('status', 'draft')
        status_info = INVOICE_STATUSES.get(status, INVOICE_STATUSES['draft'])
        status_badge = ctk.CTkLabel(
            row,
            text=status_info['label'],
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color=status_info['color'],
            fg_color=COLORS['bg_dark'],
            corner_radius=4,
            width=70,
            height=22
        )
        status_badge.pack(side="left", padx=SPACING['xs'])

        # Total
        total = ctk.CTkLabel(
            row,
            text=f"${invoice.get('total', 0):,.2f}",
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            text_color=COLORS['fg'],
            width=100,
            anchor="e"
        )
        total.pack(side="left", padx=SPACING['xs'])

        # Actions
        actions = ctk.CTkFrame(row, fg_color="transparent", width=120)
        actions.pack(side="right", padx=SPACING['xs'])
        actions.pack_propagate(False)

        # Edit button
        edit_btn = ctk.CTkButton(
            actions,
            text="\u270E",  # Edit icon
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=30,
            height=30,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=lambda inv=invoice: self._on_edit_invoice(inv)
        )
        edit_btn.pack(side="left")

        # PDF button
        pdf_btn = ctk.CTkButton(
            actions,
            text="\U0001f4c4",  # Document icon
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=30,
            height=30,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=lambda inv=invoice: self._on_export_pdf(inv)
        )
        pdf_btn.pack(side="left")

        # Status change button (if not paid)
        if status != 'paid':
            if status == 'draft':
                next_status = 'sent'
                btn_text = "Send"
            elif status == 'sent':
                next_status = 'paid'
                btn_text = "Paid"
            else:
                next_status = None
                btn_text = None

            if btn_text:
                status_btn = ctk.CTkButton(
                    actions,
                    text=btn_text,
                    font=ctk.CTkFont(family="Inter", size=10),
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover'],
                    width=50,
                    height=26,
                    corner_radius=4,
                    text_color="#ffffff",
                    command=lambda inv=invoice, ns=next_status: self._on_status_change(inv, ns)
                )
                status_btn.pack(side="left", padx=2)

        return row

    def _on_filter_change(self, value):
        """Handle status filter change."""
        self.refresh()

    def _on_new_invoice(self):
        """Create a new invoice."""
        dialog = InvoiceEditorDialog(self.winfo_toplevel(), self.business)
        self.wait_window(dialog)
        self.refresh()

    def _on_edit_invoice(self, invoice: dict):
        """Edit an existing invoice."""
        dialog = InvoiceEditorDialog(self.winfo_toplevel(), self.business, invoice)
        self.wait_window(dialog)
        self.refresh()

    def _on_export_pdf(self, invoice: dict):
        """Export invoice to PDF."""
        # Get default filename
        inv_num = invoice.get('invoice_number', 'invoice')
        default_name = f"{inv_num}.pdf"

        # Get save path
        filepath = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Export Invoice as PDF",
            initialfile=default_name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not filepath:
            return

        # Generate PDF
        success = self.business.generate_invoice_pdf(invoice['id'], filepath)

        if success:
            messagebox.showinfo(
                "PDF Exported",
                f"Invoice exported to:\n{filepath}",
                parent=self.winfo_toplevel()
            )
        else:
            messagebox.showerror(
                "Export Failed",
                "Failed to generate PDF.\nMake sure reportlab is installed.",
                parent=self.winfo_toplevel()
            )

    def _on_status_change(self, invoice: dict, new_status: str):
        """Change invoice status."""
        self.business.update_invoice_status(invoice['id'], new_status)
        self.refresh()


class InvoiceEditorDialog(ctk.CTkToplevel):
    """Dialog for creating/editing invoices."""

    def __init__(self, parent, business, invoice: dict = None):
        super().__init__(parent)

        self.business = business
        self.client_manager = get_client_manager()
        self.invoice = invoice
        self.is_edit = invoice is not None
        self.item_widgets = []

        self.title("Edit Invoice" if self.is_edit else "New Invoice")
        self.geometry("580x450")
        self.minsize(500, 400)
        self.resizable(True, True)

        self.configure(fg_color=COLORS['bg_main'])
        self.transient(parent)
        self.grab_set()

        self._build_ui()

        if self.is_edit:
            self._load_invoice()

    def _build_ui(self):
        """Build editor UI with grid layout."""
        # Main container
        main = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=6)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Use grid for main layout
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(4, weight=1)  # Items section expands

        # === ROW 0: Client ===
        ctk.CTkLabel(
            main, text="Client:", font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg']
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(12, 4))

        clients = self.client_manager.get_clients()
        client_names = ["Select Client..."] + [c['name'] for c in clients]
        self.clients_map = {c['name']: c['id'] for c in clients}

        self.client_var = ctk.StringVar(value="Select Client...")
        self.client_dropdown = ctk.CTkOptionMenu(
            main, variable=self.client_var, values=client_names,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'], button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'], dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            width=200, height=32, corner_radius=4
        )
        self.client_dropdown.grid(row=0, column=1, sticky="w", padx=0, pady=(12, 4))

        # === ROW 1: Due Date + Tax ===
        row1 = ctk.CTkFrame(main, fg_color="transparent")
        row1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

        ctk.CTkLabel(
            row1, text="Due Date:", font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        default_due = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        self.due_picker = DatePickerWidget(row1, initial_date=default_due)
        self.due_picker.pack(side="left", padx=(8, 24))

        ctk.CTkLabel(
            row1, text="Tax %:", font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        self.tax_entry = ctk.CTkEntry(
            row1, font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            width=50, height=32
        )
        self.tax_entry.pack(side="left", padx=8)
        self.tax_entry.insert(0, "0")
        self.tax_entry.bind('<KeyRelease>', lambda e: self._update_totals())

        # === ROW 2: Items header ===
        items_header = ctk.CTkFrame(main, fg_color="transparent")
        items_header.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            items_header, text="Items",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        ctk.CTkButton(
            items_header, text="+ Add", font=ctk.CTkFont(family="Inter", size=10),
            fg_color=COLORS['bg_hover'], hover_color=COLORS['accent'],
            height=24, width=60, corner_radius=4,
            command=self._add_item_row
        ).pack(side="right")

        ctk.CTkButton(
            items_header, text="Catalog", font=ctk.CTkFont(family="Inter", size=10),
            fg_color="transparent", hover_color=COLORS['bg_hover'],
            height=24, width=60, corner_radius=4, text_color=COLORS['accent'],
            command=self._show_catalog_picker
        ).pack(side="right", padx=4)

        # === ROW 3: Items column headers ===
        col_header = ctk.CTkFrame(main, fg_color=COLORS['bg_dark'], height=28, corner_radius=4)
        col_header.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 2))
        col_header.pack_propagate(False)

        cols = [("Description", 200), ("Qty", 50), ("Price", 70), ("Total", 70), ("", 30)]
        for txt, w in cols:
            ctk.CTkLabel(
                col_header, text=txt, font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                text_color=COLORS['fg_dim'], width=w, anchor="w"
            ).pack(side="left", padx=4, pady=4)

        # === ROW 4: Items list (scrollable, expands) ===
        self.items_scroll = ctk.CTkScrollableFrame(
            main, fg_color=COLORS['bg_dark'], corner_radius=4,
            scrollbar_button_color=COLORS['bg_hover']
        )
        self.items_scroll.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=12, pady=2)
        self.items_list = self.items_scroll

        # === ROW 5: Totals ===
        totals = ctk.CTkFrame(main, fg_color="transparent")
        totals.grid(row=5, column=0, columnspan=2, sticky="e", padx=12, pady=8)

        self.subtotal_label = ctk.CTkLabel(
            totals, text="Subtotal: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=COLORS['fg_secondary']
        )
        self.subtotal_label.pack(side="left", padx=12)

        self.tax_label = ctk.CTkLabel(
            totals, text="Tax: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=COLORS['fg_secondary']
        )
        self.tax_label.pack(side="left", padx=12)

        self.total_label = ctk.CTkLabel(
            totals, text="Total: $0.00",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color=COLORS['accent']
        )
        self.total_label.pack(side="left", padx=12)

        # === ROW 6: Notes ===
        notes_row = ctk.CTkFrame(main, fg_color="transparent")
        notes_row.grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            notes_row, text="Notes:", font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        ).pack(side="left")

        self.notes_text = ctk.CTkEntry(
            notes_row, font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=32, placeholder_text="Optional notes..."
        )
        self.notes_text.pack(side="left", fill="x", expand=True, padx=8)

        # === Buttons (outside main frame) ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        if self.is_edit:
            ctk.CTkButton(
                btn_frame, text="Delete", font=ctk.CTkFont(family="Inter", size=12),
                fg_color="#EF4444", hover_color="#DC2626",
                height=36, width=80, corner_radius=4, text_color="#ffffff",
                command=self._on_delete
            ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Cancel", font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'], hover_color=COLORS['bg_dark'],
            height=36, width=80, corner_radius=4, text_color=COLORS['fg_secondary'],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Save", font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            height=36, width=100, corner_radius=4, text_color="#ffffff",
            command=self._on_save
        ).pack(side="right")

    def _add_item_row(self, description: str = "", qty: int = 1, price: float = 0.0, item_id: int = None):
        """Add an item row to the items list."""
        row = ctk.CTkFrame(self.items_list, fg_color="transparent", height=34)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        row.item_id = item_id

        # Description (width=200 to match header)
        desc_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            width=200, height=28, placeholder_text="Description"
        )
        desc_entry.pack(side="left", padx=4)
        if description:
            desc_entry.insert(0, description)
        row.desc_entry = desc_entry

        # Quantity (width=50)
        qty_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            width=50, height=28, justify="center"
        )
        qty_entry.pack(side="left", padx=4)
        qty_entry.insert(0, str(qty))
        qty_entry.bind('<KeyRelease>', lambda e, r=row: self._update_row_total(r))
        row.qty_entry = qty_entry

        # Price (width=70)
        price_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            width=70, height=28, justify="right"
        )
        price_entry.pack(side="left", padx=4)
        price_entry.insert(0, f"{price:.2f}")
        price_entry.bind('<KeyRelease>', lambda e, r=row: self._update_row_total(r))
        row.price_entry = price_entry

        # Total (width=70)
        total_label = ctk.CTkLabel(
            row, text=f"${qty * price:.2f}",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=COLORS['fg'], width=70, anchor="e"
        )
        total_label.pack(side="left", padx=4)
        row.total_label = total_label

        # Delete button (width=30)
        ctk.CTkButton(
            row, text="×", font=ctk.CTkFont(size=14),
            fg_color="transparent", hover_color="#EF4444",
            width=28, height=28, corner_radius=4,
            text_color=COLORS['fg_dim'],
            command=lambda r=row: self._remove_item_row(r)
        ).pack(side="left", padx=2)

        self.item_widgets.append(row)
        self._update_totals()

    def _remove_item_row(self, row):
        """Remove an item row."""
        row.destroy()
        self.item_widgets.remove(row)
        self._update_totals()

    def _update_row_total(self, row):
        """Update a row's total based on qty and price."""
        try:
            qty = int(row.qty_entry.get() or 0)
            price = float(row.price_entry.get() or 0)
            total = qty * price
            row.total_label.configure(text=f"${total:.2f}")
            self._update_totals()
        except ValueError:
            pass

    def _update_totals(self):
        """Update subtotal, tax, and total displays."""
        subtotal = 0
        for row in self.item_widgets:
            try:
                qty = int(row.qty_entry.get() or 0)
                price = float(row.price_entry.get() or 0)
                subtotal += qty * price
            except ValueError:
                pass

        try:
            tax_rate = float(self.tax_entry.get() or 0)
        except ValueError:
            tax_rate = 0

        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount

        self.subtotal_label.configure(text=f"Subtotal: ${subtotal:.2f}")
        self.tax_label.configure(text=f"Tax ({tax_rate:.1f}%): ${tax_amount:.2f}")
        self.total_label.configure(text=f"Total: ${total:.2f}")

    def _show_catalog_picker(self):
        """Show product catalog picker."""
        products = self.business.get_products()

        if not products:
            messagebox.showinfo(
                "No Products",
                "No products in catalog.\nAdd products in the Catalog tab first.",
                parent=self
            )
            return

        # Create picker dialog
        picker = ctk.CTkToplevel(self)
        picker.title("Add from Catalog")
        picker.geometry("400x400")
        picker.transient(self)
        picker.grab_set()

        # List products
        scroll = ctk.CTkScrollableFrame(picker, fg_color=COLORS['bg_card'])
        scroll.pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['md'])

        for product in products:
            row = ctk.CTkFrame(scroll, fg_color=COLORS['bg_dark'], corner_radius=4, height=50)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            name = ctk.CTkLabel(
                row,
                text=product['title'],
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg']
            )
            name.pack(side="left", padx=SPACING['md'])

            price = ctk.CTkLabel(
                row,
                text=f"${product['price']:.2f}",
                font=ctk.CTkFont(family="JetBrains Mono", size=12),
                text_color=COLORS['accent']
            )
            price.pack(side="left", padx=SPACING['sm'])

            add_btn = ctk.CTkButton(
                row,
                text="Add",
                font=ctk.CTkFont(family="Inter", size=11),
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                height=28,
                width=50,
                corner_radius=4,
                text_color="#ffffff",
                command=lambda p=product, pk=picker: self._add_from_catalog(p, pk)
            )
            add_btn.pack(side="right", padx=SPACING['md'])

    def _add_from_catalog(self, product: dict, picker):
        """Add a product from catalog to items."""
        self._add_item_row(
            description=product['title'],
            qty=1,
            price=product['price']
        )
        picker.destroy()

    def _load_invoice(self):
        """Load existing invoice data."""
        if not self.invoice:
            return

        # Set client
        client_name = self.invoice.get('client_name')
        if client_name:
            self.client_var.set(client_name)

        # Set due date
        due = self.invoice.get('due_date', '')
        if due:
            self.due_picker.set_date(due)

        # Set tax rate
        tax = self.invoice.get('tax_rate', 0)
        self.tax_entry.delete(0, 'end')
        self.tax_entry.insert(0, str(tax))

        # Set notes
        notes = self.invoice.get('notes', '')
        if notes:
            self.notes_text.insert(0, notes)

        # Load items
        items = self.business.get_invoice_items(self.invoice['id'])
        for item in items:
            self._add_item_row(
                description=item['description'],
                qty=item['quantity'],
                price=item['unit_price'],
                item_id=item['id']
            )

    def _on_save(self):
        """Save invoice."""
        # Get client ID
        client_name = self.client_var.get()
        client_id = self.clients_map.get(client_name)

        if not client_id:
            messagebox.showerror("Error", "Please select a client.", parent=self)
            return

        # Get data
        due_date = self.due_picker.get_date()
        try:
            tax_rate = float(self.tax_entry.get() or 0)
        except ValueError:
            tax_rate = 0

        notes = self.notes_text.get().strip()

        # Create or update invoice
        if self.is_edit:
            invoice_id = self.invoice['id']
            self.business.update_invoice(invoice_id, {
                'client_id': client_id,
                'due_date': due_date,
                'tax_rate': tax_rate,
                'notes': notes
            })

            # Delete existing items and re-add
            existing_items = self.business.get_invoice_items(invoice_id)
            for item in existing_items:
                self.business.delete_invoice_item(item['id'])
        else:
            invoice_id = self.business.create_invoice({
                'client_id': client_id,
                'due_date': due_date,
                'tax_rate': tax_rate,
                'notes': notes
            })

        # Add items
        for row in self.item_widgets:
            desc = row.desc_entry.get().strip()
            if not desc:
                continue
            try:
                qty = int(row.qty_entry.get() or 1)
                price = float(row.price_entry.get() or 0)
            except ValueError:
                continue

            self.business.add_invoice_item(invoice_id, {
                'description': desc,
                'quantity': qty,
                'unit_price': price
            })

        self.destroy()

    def _on_delete(self):
        """Delete invoice."""
        if messagebox.askyesno(
            "Delete Invoice",
            f"Are you sure you want to delete invoice {self.invoice.get('invoice_number', '')}?",
            parent=self
        ):
            self.business.delete_invoice(self.invoice['id'])
            self.destroy()
