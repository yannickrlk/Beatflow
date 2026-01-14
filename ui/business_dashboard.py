"""Business Dashboard for ProducerOS - Overview of financial health."""

import customtkinter as ctk
from datetime import datetime
from ui.theme import COLORS, SPACING
from core.business import get_business_manager, INCOME_CATEGORIES


class BusinessDashboard(ctk.CTkFrame):
    """Dashboard showing revenue, expenses, goals, and recent transactions."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.business = get_business_manager()
        self._build_ui()

    def _build_ui(self):
        """Build the dashboard UI."""
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.scroll.pack(fill="both", expand=True)

        # Top row: Stats cards
        self.stats_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, SPACING['lg']))

        # Create stat cards
        self.stat_cards = {}
        stats = [
            ("revenue", "Revenue (Month)", "$0.00", COLORS['accent'], None),
            ("expenses", "Expenses (Month)", "$0.00", "#EF4444", None),
            ("profit", "Net Profit", "$0.00", "#22C55E", None),
            ("outstanding", "Outstanding", "$0.00", "#3B82F6", "Total of unpaid invoices (Sent status)")
        ]

        for i, (key, label, value, color, tooltip) in enumerate(stats):
            card = self._create_stat_card(self.stats_frame, label, value, color, tooltip)
            card.grid(row=0, column=i, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")
            self.stat_cards[key] = card
            self.stats_frame.grid_columnconfigure(i, weight=1)

        # Middle row: Goal progress + Income by source
        self.middle_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.middle_frame.pack(fill="x", pady=(0, SPACING['lg']))
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=1)

        # Goal progress card
        self.goal_card = self._create_goal_card(self.middle_frame)
        self.goal_card.grid(row=0, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")

        # Income breakdown card
        self.income_card = self._create_income_breakdown_card(self.middle_frame)
        self.income_card.grid(row=0, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")

        # Bottom row: Recent transactions
        self.recent_frame = self._create_recent_transactions_card(self.scroll)
        self.recent_frame.pack(fill="x", pady=(0, SPACING['lg']))

    def _create_stat_card(self, parent, label: str, value: str, accent_color: str, tooltip: str = None) -> ctk.CTkFrame:
        """Create a statistics card with optional tooltip."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            height=100
        )
        card.pack_propagate(False)

        # Colored accent bar at top
        accent = ctk.CTkFrame(card, fg_color=accent_color, height=3, corner_radius=0)
        accent.pack(fill="x")

        # Content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['sm'])

        # Label row (with optional info icon)
        label_frame = ctk.CTkFrame(content, fg_color="transparent")
        label_frame.pack(anchor="w", fill="x")

        lbl = ctk.CTkLabel(
            label_frame,
            text=label,
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        lbl.pack(side="left")

        # Add info icon with tooltip if provided
        if tooltip:
            info_btn = ctk.CTkLabel(
                label_frame,
                text=" \u24D8",  # Circled i
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_dim'],
                cursor="hand2"
            )
            info_btn.pack(side="left", padx=(4, 0))

            # Create tooltip
            self._create_tooltip(info_btn, tooltip)

        # Value
        val_lbl = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(family="JetBrains Mono", size=24, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        val_lbl.pack(anchor="w", pady=(SPACING['xs'], 0))

        # Store reference for updates
        card.value_label = val_lbl

        return card

    def _create_tooltip(self, widget, text: str):
        """Create a hover tooltip for a widget."""
        tooltip_window = None

        def show_tooltip(event):
            nonlocal tooltip_window
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20

            tooltip_window = ctk.CTkToplevel(widget)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{x}+{y}")
            tooltip_window.attributes("-topmost", True)

            label = ctk.CTkLabel(
                tooltip_window,
                text=text,
                font=ctk.CTkFont(family="Inter", size=11),
                fg_color=COLORS['bg_dark'],
                text_color=COLORS['fg'],
                corner_radius=4,
                padx=8,
                pady=4
            )
            label.pack()

        def hide_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def _create_goal_card(self, parent) -> ctk.CTkFrame:
        """Create the monthly goal progress card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=8
        )

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        title = ctk.CTkLabel(
            header,
            text="Monthly Goal",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(side="left")

        # Set goal button
        set_btn = ctk.CTkButton(
            header,
            text="Set Goal",
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            height=28,
            width=70,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self._on_set_goal
        )
        set_btn.pack(side="right")

        # Progress area
        progress_frame = ctk.CTkFrame(card, fg_color="transparent")
        progress_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        # Amount label
        self.goal_amount_label = ctk.CTkLabel(
            progress_frame,
            text="$0 / $0",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        self.goal_amount_label.pack(anchor="w")

        # Progress bar
        self.goal_progress = ctk.CTkProgressBar(
            progress_frame,
            height=12,
            corner_radius=6,
            fg_color=COLORS['bg_dark'],
            progress_color=COLORS['accent']
        )
        self.goal_progress.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))
        self.goal_progress.set(0)

        # Percentage label
        self.goal_percent_label = ctk.CTkLabel(
            progress_frame,
            text="0% of goal",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        )
        self.goal_percent_label.pack(anchor="w")

        # Spacer
        ctk.CTkFrame(card, fg_color="transparent", height=SPACING['md']).pack()

        return card

    def _create_income_breakdown_card(self, parent) -> ctk.CTkFrame:
        """Create income by category breakdown card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=8
        )

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        title = ctk.CTkLabel(
            header,
            text="Income Sources",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(side="left")

        # Category bars container
        self.income_bars_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.income_bars_frame.pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['sm'])

        return card

    def _create_recent_transactions_card(self, parent) -> ctk.CTkFrame:
        """Create recent transactions card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=8
        )

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        title = ctk.CTkLabel(
            header,
            text="Recent Transactions",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(side="left")

        # View all button
        view_all_btn = ctk.CTkButton(
            header,
            text="View All",
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            height=28,
            corner_radius=4,
            text_color=COLORS['accent'],
            command=self._on_view_all_transactions
        )
        view_all_btn.pack(side="right")

        # Transactions list
        self.transactions_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.transactions_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        return card

    def refresh(self):
        """Refresh dashboard data."""
        # Get current month stats
        now = datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')

        stats = self.business.get_revenue_stats(start_date, end_date)
        invoice_stats = self.business.get_invoice_stats()

        # Update stat cards
        self.stat_cards['revenue'].value_label.configure(
            text=f"${stats['total_income']:,.2f}"
        )
        self.stat_cards['expenses'].value_label.configure(
            text=f"${stats['total_expenses']:,.2f}"
        )
        self.stat_cards['profit'].value_label.configure(
            text=f"${stats['net_profit']:,.2f}",
            text_color="#22C55E" if stats['net_profit'] >= 0 else "#EF4444"
        )
        self.stat_cards['outstanding'].value_label.configure(
            text=f"${invoice_stats['outstanding_total']:,.2f}"
        )

        # Update goal progress
        goal_data = self.business.get_goal_progress()
        if goal_data['has_goal']:
            self.goal_amount_label.configure(
                text=f"${goal_data['current']:,.2f} / ${goal_data['target']:,.2f}"
            )
            self.goal_progress.set(goal_data['percentage'] / 100)
            self.goal_percent_label.configure(
                text=f"{goal_data['percentage']:.0f}% of goal"
            )
        else:
            self.goal_amount_label.configure(text="No goal set")
            self.goal_progress.set(0)
            self.goal_percent_label.configure(text="Set a monthly income goal")

        # Update income breakdown
        self._update_income_breakdown(stats['income_by_category'], stats['total_income'])

        # Update recent transactions
        self._update_recent_transactions()

    def _update_income_breakdown(self, categories: list, total: float):
        """Update income breakdown bars."""
        # Clear existing
        for widget in self.income_bars_frame.winfo_children():
            widget.destroy()

        if not categories or total == 0:
            empty = ctk.CTkLabel(
                self.income_bars_frame,
                text="No income recorded this month",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_dim']
            )
            empty.pack(pady=SPACING['lg'])
            return

        # Colors for categories
        colors = ["#FF6B35", "#3B82F6", "#22C55E", "#A855F7", "#F59E0B"]

        for i, cat in enumerate(categories[:5]):  # Max 5 categories
            row = ctk.CTkFrame(self.income_bars_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Category name
            name = ctk.CTkLabel(
                row,
                text=cat['category'] or "Other",
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_secondary'],
                width=120,
                anchor="w"
            )
            name.pack(side="left")

            # Progress bar
            pct = (cat['total'] / total) if total > 0 else 0
            bar = ctk.CTkProgressBar(
                row,
                height=8,
                corner_radius=4,
                fg_color=COLORS['bg_dark'],
                progress_color=colors[i % len(colors)]
            )
            bar.pack(side="left", fill="x", expand=True, padx=SPACING['sm'])
            bar.set(pct)

            # Amount
            amount = ctk.CTkLabel(
                row,
                text=f"${cat['total']:,.2f}",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color=COLORS['fg'],
                width=80,
                anchor="e"
            )
            amount.pack(side="right")

    def _update_recent_transactions(self):
        """Update recent transactions list."""
        # Clear existing
        for widget in self.transactions_frame.winfo_children():
            widget.destroy()

        transactions = self.business.get_recent_transactions(5)

        if not transactions:
            empty = ctk.CTkLabel(
                self.transactions_frame,
                text="No transactions yet",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_dim']
            )
            empty.pack(pady=SPACING['lg'])
            return

        for txn in transactions:
            row = ctk.CTkFrame(self.transactions_frame, fg_color="transparent", height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Type indicator
            is_income = txn.get('type') == 'income'
            indicator = ctk.CTkLabel(
                row,
                text="+" if is_income else "-",
                font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
                text_color="#22C55E" if is_income else "#EF4444",
                width=20
            )
            indicator.pack(side="left")

            # Description
            desc = ctk.CTkLabel(
                row,
                text=txn.get('description', txn.get('category', 'Transaction'))[:40],
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg'],
                anchor="w"
            )
            desc.pack(side="left", fill="x", expand=True, padx=SPACING['sm'])

            # Date
            date_str = txn.get('date', '')
            date_lbl = ctk.CTkLabel(
                row,
                text=date_str,
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_dim'],
                width=80
            )
            date_lbl.pack(side="right", padx=SPACING['sm'])

            # Amount
            amount_str = f"${txn.get('amount', 0):,.2f}"
            amount = ctk.CTkLabel(
                row,
                text=amount_str,
                font=ctk.CTkFont(family="JetBrains Mono", size=12),
                text_color="#22C55E" if is_income else "#EF4444",
                width=80,
                anchor="e"
            )
            amount.pack(side="right")

    def _on_set_goal(self):
        """Open set goal dialog."""
        dialog = SetGoalDialog(self.winfo_toplevel(), self.business)
        self.wait_window(dialog)
        self.refresh()

    def _on_view_all_transactions(self):
        """Switch to ledger tab - handled by parent."""
        parent = self.master.master  # BusinessView
        if hasattr(parent, '_on_tab_change'):
            parent._on_tab_change('ledger')


class SetGoalDialog(ctk.CTkToplevel):
    """Dialog for setting monthly income goal."""

    def __init__(self, parent, business):
        super().__init__(parent)

        self.business = business

        self.title("Set Monthly Goal")
        self.geometry("380x250")
        self.minsize(320, 200)
        self.resizable(True, True)
        self.configure(fg_color=COLORS['bg_main'])

        # Center on parent
        self.transient(parent)
        self.grab_set()

        self._build_ui()

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

        # Title
        title = ctk.CTkLabel(
            scroll,
            text="Set Your Monthly Income Goal",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(pady=(SPACING['md'], SPACING['lg']))

        # Amount input
        input_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        input_frame.pack(fill="x", padx=SPACING['lg'])

        dollar_sign = ctk.CTkLabel(
            input_frame,
            text="$",
            font=ctk.CTkFont(family="JetBrains Mono", size=24),
            text_color=COLORS['fg']
        )
        dollar_sign.pack(side="left")

        self.amount_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(family="JetBrains Mono", size=20),
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            height=48,
            placeholder_text="1000"
        )
        self.amount_entry.pack(side="left", fill="x", expand=True, padx=SPACING['xs'])

        # Load existing goal
        existing = self.business.get_monthly_goal()
        if existing:
            self.amount_entry.insert(0, str(int(existing['target_amount'])))

        # Buttons (fixed at bottom, outside scroll)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_dark'],
            height=36,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self.destroy
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, SPACING['xs']))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Goal",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=36,
            corner_radius=4,
            text_color="#ffffff",
            command=self._on_save
        )
        save_btn.pack(side="right", expand=True, fill="x", padx=(SPACING['xs'], 0))

    def _on_save(self):
        """Save the goal."""
        try:
            amount = float(self.amount_entry.get().replace(',', ''))
            if amount > 0:
                self.business.set_monthly_goal(amount)
                self.destroy()
        except ValueError:
            pass
