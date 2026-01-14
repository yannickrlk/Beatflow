"""Catalog View for ProducerOS - Product and service management."""

import customtkinter as ctk
from tkinter import messagebox
from ui.theme import COLORS, SPACING
from core.business import get_business_manager


class CatalogView(ctk.CTkFrame):
    """View for managing products and services."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.business = get_business_manager()
        self.product_widgets = []

        self._build_ui()

    def _build_ui(self):
        """Build the catalog view UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING['md']))

        # Title
        title = ctk.CTkLabel(
            header,
            text="Product & Service Catalog",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(side="left")

        # Add product button
        add_btn = ctk.CTkButton(
            header,
            text="+ Add Item",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=36,
            corner_radius=4,
            text_color="#ffffff",
            command=self._on_add_product
        )
        add_btn.pack(side="right")

        # Type filter
        self.type_var = ctk.StringVar(value="All")
        type_filter = ctk.CTkSegmentedButton(
            header,
            values=["All", "Licenses", "Services"],
            variable=self.type_var,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=200,
            height=32,
            corner_radius=4,
            command=self._on_filter_change
        )
        type_filter.pack(side="right", padx=SPACING['md'])

        # Products grid
        self.products_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.products_scroll.pack(fill="both", expand=True)

        # Grid container
        self.grid_container = ctk.CTkFrame(self.products_scroll, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.products_scroll, fg_color="transparent")

        empty_icon = ctk.CTkLabel(
            self.empty_frame,
            text="\U0001f3f7",  # Label/tag emoji
            font=ctk.CTkFont(size=48),
            text_color=COLORS['fg_dim']
        )
        empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

        empty_msg = ctk.CTkLabel(
            self.empty_frame,
            text="No Products Yet",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        empty_msg.pack()

        empty_submsg = ctk.CTkLabel(
            self.empty_frame,
            text="Add your beat licenses and services\nto use them quickly in invoices.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary'],
            justify="center"
        )
        empty_submsg.pack(pady=(SPACING['sm'], SPACING['lg']))

        empty_btn = ctk.CTkButton(
            self.empty_frame,
            text="+ Add Product",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=44,
            width=160,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_add_product
        )
        empty_btn.pack()

    def refresh(self):
        """Refresh product list."""
        # Clear existing
        for widget in self.product_widgets:
            widget.destroy()
        self.product_widgets = []

        # Get filter
        type_filter = self.type_var.get().lower()

        products = self.business.get_products(active_only=True)

        # Apply type filter
        if type_filter == "licenses":
            products = [p for p in products if p['type'] == 'license']
        elif type_filter == "services":
            products = [p for p in products if p['type'] == 'service']

        if not products:
            self.grid_container.pack_forget()
            self.empty_frame.pack(expand=True)
            return

        self.empty_frame.pack_forget()
        self.grid_container.pack(fill="both", expand=True)

        # Create product cards in grid
        for i, product in enumerate(products):
            row = i // 3
            col = i % 3

            card = self._create_product_card(product)
            card.grid(row=row, column=col, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")
            self.product_widgets.append(card)

            self.grid_container.grid_columnconfigure(col, weight=1)

    def _create_product_card(self, product: dict) -> ctk.CTkFrame:
        """Create a product card."""
        card = ctk.CTkFrame(
            self.grid_container,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            width=220,
            height=140
        )

        # Type badge
        type_color = COLORS['accent'] if product['type'] == 'license' else "#A855F7"
        type_badge = ctk.CTkLabel(
            card,
            text=product['type'].upper(),
            font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
            text_color=type_color,
            fg_color=COLORS['bg_dark'],
            corner_radius=4,
            width=60,
            height=18
        )
        type_badge.place(x=SPACING['sm'], y=SPACING['sm'])

        # Title
        title = ctk.CTkLabel(
            card,
            text=product['title'],
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        title.place(x=SPACING['sm'], y=35)

        # Description
        desc = product.get('description', '')[:40]
        if desc:
            desc_label = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_secondary'],
                anchor="w"
            )
            desc_label.place(x=SPACING['sm'], y=60)

        # Price
        price_label = ctk.CTkLabel(
            card,
            text=f"${product['price']:.2f}",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            text_color=COLORS['accent']
        )
        price_label.place(x=SPACING['sm'], y=90)

        # Edit button
        edit_btn = ctk.CTkButton(
            card,
            text="\u270E",  # Edit icon
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=30,
            height=30,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=lambda p=product: self._on_edit_product(p)
        )
        edit_btn.place(x=175, y=SPACING['sm'])

        return card

    def _on_filter_change(self, value):
        """Handle filter change."""
        self.refresh()

    def _on_add_product(self):
        """Add a new product."""
        dialog = ProductDialog(self.winfo_toplevel(), self.business)
        self.wait_window(dialog)
        self.refresh()

    def _on_edit_product(self, product: dict):
        """Edit a product."""
        dialog = ProductDialog(self.winfo_toplevel(), self.business, product)
        self.wait_window(dialog)
        self.refresh()


class ProductDialog(ctk.CTkToplevel):
    """Dialog for creating/editing products."""

    def __init__(self, parent, business, product: dict = None):
        super().__init__(parent)

        self.business = business
        self.product = product
        self.is_edit = product is not None

        self.title("Edit Product" if self.is_edit else "Add Product")
        self.geometry("420x400")
        self.minsize(360, 300)
        self.resizable(True, True)
        self.configure(fg_color=COLORS['bg_main'])

        self.transient(parent)
        self.grab_set()

        self._build_ui()

        if self.is_edit:
            self._load_product()

    def _build_ui(self):
        """Build dialog UI with scrollable content."""
        # Grid layout for proper expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS['bg_card'], corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # Title field
        title_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        title_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        title_label = ctk.CTkLabel(
            title_frame,
            text="Title:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg'],
            width=80,
            anchor="w"
        )
        title_label.pack(side="left")

        self.title_entry = ctk.CTkEntry(
            title_frame,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            height=36,
            placeholder_text="e.g., WAV Lease"
        )
        self.title_entry.pack(side="left", fill="x", expand=True, padx=SPACING['xs'])

        # Type dropdown
        type_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        type_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        type_label = ctk.CTkLabel(
            type_frame,
            text="Type:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg'],
            width=80,
            anchor="w"
        )
        type_label.pack(side="left")

        self.type_var = ctk.StringVar(value="license")
        self.type_dropdown = ctk.CTkSegmentedButton(
            type_frame,
            values=["license", "service"],
            variable=self.type_var,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=180,
            height=32,
            corner_radius=4
        )
        self.type_dropdown.pack(side="left", padx=SPACING['xs'])

        # Price field
        price_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        price_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        price_label = ctk.CTkLabel(
            price_frame,
            text="Price:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg'],
            width=80,
            anchor="w"
        )
        price_label.pack(side="left")

        dollar = ctk.CTkLabel(
            price_frame,
            text="$",
            font=ctk.CTkFont(family="JetBrains Mono", size=14),
            text_color=COLORS['fg']
        )
        dollar.pack(side="left")

        self.price_entry = ctk.CTkEntry(
            price_frame,
            font=ctk.CTkFont(family="JetBrains Mono", size=14),
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            width=100,
            height=36,
            placeholder_text="0.00"
        )
        self.price_entry.pack(side="left", padx=SPACING['xs'])

        # Description field
        desc_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        desc_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        desc_label = ctk.CTkLabel(
            desc_frame,
            text="Description:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg']
        )
        desc_label.pack(anchor="w")

        self.desc_entry = ctk.CTkEntry(
            desc_frame,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            height=36,
            placeholder_text="Short description (optional)"
        )
        self.desc_entry.pack(fill="x", pady=SPACING['xs'])

        # Buttons (fixed at bottom, outside scroll)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

        if self.is_edit:
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="Delete",
                font=ctk.CTkFont(family="Inter", size=12),
                fg_color="#EF4444",
                hover_color="#DC2626",
                height=40,
                corner_radius=4,
                text_color="#ffffff",
                command=self._on_delete
            )
            delete_btn.pack(side="left")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_dark'],
            height=40,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(SPACING['xs'], 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=40,
            corner_radius=4,
            text_color="#ffffff",
            command=self._on_save
        )
        save_btn.pack(side="right")

    def _load_product(self):
        """Load existing product data."""
        if not self.product:
            return

        self.title_entry.insert(0, self.product.get('title', ''))
        self.type_var.set(self.product.get('type', 'license'))
        self.price_entry.insert(0, f"{self.product.get('price', 0):.2f}")

        desc = self.product.get('description', '')
        if desc:
            self.desc_entry.insert(0, desc)

    def _on_save(self):
        """Save product."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Please enter a title.", parent=self)
            return

        try:
            price = float(self.price_entry.get().replace(',', ''))
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid price.", parent=self)
            return

        data = {
            'title': title,
            'type': self.type_var.get(),
            'price': price,
            'description': self.desc_entry.get().strip()
        }

        if self.is_edit:
            self.business.update_product(self.product['id'], data)
        else:
            self.business.add_product(data)

        self.destroy()

    def _on_delete(self):
        """Delete product."""
        if messagebox.askyesno(
            "Delete Product",
            f"Delete '{self.product.get('title', '')}'?",
            parent=self
        ):
            self.business.delete_product(self.product['id'])
            self.destroy()
