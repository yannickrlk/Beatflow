"""Productivity Dashboard - Charts and insights for task completion."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta

# Try to import matplotlib for charts
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ProductivityDashboard(ctk.CTkFrame):
    """Dashboard with productivity charts and insights."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the dashboard UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['sm']))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Productivity Dashboard",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        # Refresh button
        ctk.CTkButton(
            header,
            text="Refresh",
            font=ctk.CTkFont(family="Inter", size=12),
            width=80,
            height=32,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            corner_radius=6,
            command=self.refresh
        ).pack(side="right")

        # Stats cards row
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['md'])

        # Charts area (scrollable)
        self.charts_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.charts_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['sm'])

    def refresh(self):
        """Refresh all dashboard data."""
        self._update_stats_cards()
        self._update_charts()

    def _update_stats_cards(self):
        """Update the stats cards."""
        # Clear existing
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        # Get stats
        stats = self.task_manager.get_completion_stats()
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = self.task_manager.get_focus_sessions(date=today)
        completed_sessions = sum(1 for s in sessions if s.get('completed'))
        focus_minutes = sum(s.get('duration', 0) for s in sessions if s.get('completed')) // 60

        # Stats data
        cards_data = [
            ("Today's Tasks", f"{stats['daily_completed']}/{stats['daily_total']}", COLORS['accent']),
            ("Focus Time", f"{focus_minutes}m", COLORS['accent_secondary']),
            ("Sessions", str(completed_sessions), COLORS['success']),
            ("Active Projects", str(stats['active_projects']), COLORS['fg_secondary']),
        ]

        for title, value, color in cards_data:
            card = self._create_stat_card(title, value, color)
            card.pack(side="left", padx=SPACING['sm'], expand=True, fill="x")

    def _create_stat_card(self, title: str, value: str, accent_color: str) -> ctk.CTkFrame:
        """Create a stat card widget."""
        card = ctk.CTkFrame(
            self.stats_frame,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            height=80
        )
        card.pack_propagate(False)

        # Value (big)
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(family="JetBrains Mono", size=28, weight="bold"),
            text_color=accent_color
        ).pack(pady=(SPACING['md'], 0))

        # Title (small)
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        ).pack()

        return card

    def _update_charts(self):
        """Update the charts."""
        # Clear existing
        for widget in self.charts_frame.winfo_children():
            widget.destroy()

        if MATPLOTLIB_AVAILABLE:
            self._create_matplotlib_charts()
        else:
            self._create_text_charts()

    def _create_matplotlib_charts(self):
        """Create charts using matplotlib."""
        # Configure matplotlib for dark theme
        plt.style.use('dark_background')

        # Row 1: Weekly completion + Context breakdown
        row1 = ctk.CTkFrame(self.charts_frame, fg_color="transparent")
        row1.pack(fill="x", pady=SPACING['sm'])

        self._create_weekly_chart(row1)
        self._create_context_chart(row1)

        # Row 2: Focus sessions timeline
        row2 = ctk.CTkFrame(self.charts_frame, fg_color="transparent")
        row2.pack(fill="x", pady=SPACING['sm'])

        self._create_focus_chart(row2)
        self._create_insights_panel(row2)

    def _create_weekly_chart(self, parent):
        """Create weekly completion bar chart."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(side="left", fill="both", expand=True, padx=(0, SPACING['sm']))

        ctk.CTkLabel(
            card,
            text="Tasks Completed (Last 7 Days)",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['xs']))

        # Get data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        stats = self.task_manager.get_completion_stats_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Build data for all 7 days
        date_counts = {s['date']: s['count'] for s in stats}
        days = []
        counts = []
        for i in range(7):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            day_name = (start_date + timedelta(days=i)).strftime('%a')
            days.append(day_name)
            counts.append(date_counts.get(date, 0))

        # Create chart
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=COLORS['bg_card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_card'])

        bars = ax.bar(days, counts, color=COLORS['accent'], width=0.6)
        ax.set_ylabel('Tasks', fontsize=9, color=COLORS['fg_secondary'])
        ax.tick_params(colors=COLORS['fg_secondary'], labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['border'])
        ax.spines['left'].set_color(COLORS['border'])

        # Add value labels on bars
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       str(count), ha='center', va='bottom',
                       fontsize=8, color=COLORS['fg'])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=SPACING['sm'], pady=SPACING['sm'])

    def _create_context_chart(self, parent):
        """Create context distribution pie chart."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(side="left", fill="both", expand=True, padx=(SPACING['sm'], 0))

        ctk.CTkLabel(
            card,
            text="Tasks by Context",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['xs']))

        # Get data
        stats = self.task_manager.get_completion_stats_by_context()

        if not stats:
            ctk.CTkLabel(
                card,
                text="No completed tasks yet",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary']
            ).pack(pady=SPACING['xl'])
            return

        # Context colors
        context_colors = {
            "@Studio": "#9B59B6",
            "@Mixing": "#3498DB",
            "@Marketing": "#E74C3C",
            "@Admin": "#95A5A6",
            "@Other": "#7F8C8D"
        }

        labels = [s['context'] or '@Other' for s in stats]
        sizes = [s['count'] for s in stats]
        colors = [context_colors.get(l, "#7F8C8D") for l in labels]

        # Create chart
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=COLORS['bg_card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_card'])

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.0f%%', startangle=90,
            textprops={'fontsize': 8, 'color': COLORS['fg']}
        )

        for autotext in autotexts:
            autotext.set_color(COLORS['fg'])
            autotext.set_fontsize(8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=SPACING['sm'], pady=SPACING['sm'])

    def _create_focus_chart(self, parent):
        """Create focus sessions chart."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(side="left", fill="both", expand=True, padx=(0, SPACING['sm']))

        ctk.CTkLabel(
            card,
            text="Focus Sessions (Last 7 Days)",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['xs']))

        # Get data for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)

        days = []
        minutes = []
        for i in range(7):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            day_name = (start_date + timedelta(days=i)).strftime('%a')
            sessions = self.task_manager.get_focus_sessions(date=date)
            total_mins = sum(s.get('duration', 0) for s in sessions if s.get('completed')) // 60
            days.append(day_name)
            minutes.append(total_mins)

        # Create chart
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=COLORS['bg_card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_card'])

        ax.fill_between(range(len(days)), minutes, color=COLORS['accent_secondary'], alpha=0.3)
        ax.plot(range(len(days)), minutes, color=COLORS['accent_secondary'], linewidth=2, marker='o', markersize=4)

        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days)
        ax.set_ylabel('Minutes', fontsize=9, color=COLORS['fg_secondary'])
        ax.tick_params(colors=COLORS['fg_secondary'], labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['border'])
        ax.spines['left'].set_color(COLORS['border'])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=SPACING['sm'], pady=SPACING['sm'])

    def _create_insights_panel(self, parent):
        """Create insights/tips panel."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(side="left", fill="both", expand=True, padx=(SPACING['sm'], 0))

        ctk.CTkLabel(
            card,
            text="Insights",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['sm']))

        # Generate insights
        insights = self._generate_insights()

        for insight in insights:
            insight_row = ctk.CTkFrame(card, fg_color="transparent")
            insight_row.pack(fill="x", padx=SPACING['md'], pady=SPACING['xs'])

            ctk.CTkLabel(
                insight_row,
                text="•",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['accent']
            ).pack(side="left", padx=(0, SPACING['xs']))

            ctk.CTkLabel(
                insight_row,
                text=insight,
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_secondary'],
                wraplength=200,
                anchor="w",
                justify="left"
            ).pack(side="left", fill="x")

    def _generate_insights(self) -> list:
        """Generate productivity insights."""
        insights = []

        # Get stats
        stats = self.task_manager.get_completion_stats()
        context_stats = self.task_manager.get_completion_stats_by_context()

        # Completion rate insight
        if stats['daily_total'] > 0:
            rate = (stats['daily_completed'] / stats['daily_total']) * 100
            if rate >= 80:
                insights.append(f"Great job! {rate:.0f}% completion rate today.")
            elif rate >= 50:
                insights.append(f"You're {rate:.0f}% done with today's tasks.")
            else:
                insights.append(f"Keep going! {stats['daily_total'] - stats['daily_completed']} tasks remaining.")

        # Most productive context
        if context_stats:
            top_context = context_stats[0]
            insights.append(f"Most active in {top_context['context'] or '@Other'} ({top_context['count']} tasks).")

        # Focus time insight
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = self.task_manager.get_focus_sessions(date=today)
        completed_sessions = sum(1 for s in sessions if s.get('completed'))
        if completed_sessions > 0:
            insights.append(f"{completed_sessions} focus sessions completed today!")
        else:
            insights.append("Try a 25-minute focus session to boost productivity.")

        # Overdue tasks warning
        if stats['overdue_tasks'] > 0:
            insights.append(f"You have {stats['overdue_tasks']} overdue tasks.")

        return insights[:4]  # Max 4 insights

    def _create_text_charts(self):
        """Create text-based charts when matplotlib is not available."""
        # Warning
        warning = ctk.CTkFrame(self.charts_frame, fg_color=COLORS['bg_card'], corner_radius=8)
        warning.pack(fill="x", pady=SPACING['sm'])

        ctk.CTkLabel(
            warning,
            text="Install matplotlib for visual charts: pip install matplotlib",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        ).pack(pady=SPACING['md'])

        # Text-based stats
        self._create_text_weekly_stats()
        self._create_text_context_stats()

    def _create_text_weekly_stats(self):
        """Create text-based weekly stats."""
        card = ctk.CTkFrame(self.charts_frame, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(fill="x", pady=SPACING['sm'])

        ctk.CTkLabel(
            card,
            text="Tasks Completed (Last 7 Days)",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['sm']))

        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        stats = self.task_manager.get_completion_stats_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        date_counts = {s['date']: s['count'] for s in stats}

        for i in range(7):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            day_name = date.strftime('%A')
            count = date_counts.get(date_str, 0)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=SPACING['lg'], pady=2)

            ctk.CTkLabel(
                row,
                text=day_name,
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary'],
                width=100,
                anchor="w"
            ).pack(side="left")

            # Simple bar
            bar_width = min(count * 20, 200)
            if bar_width > 0:
                bar = ctk.CTkFrame(row, fg_color=COLORS['accent'], height=16, width=bar_width, corner_radius=4)
                bar.pack(side="left", padx=SPACING['sm'])
                bar.pack_propagate(False)

            ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(family="JetBrains Mono", size=12),
                text_color=COLORS['fg']
            ).pack(side="left", padx=SPACING['sm'])

        # Padding at bottom
        ctk.CTkFrame(card, fg_color="transparent", height=SPACING['md']).pack()

    def _create_text_context_stats(self):
        """Create text-based context stats."""
        card = ctk.CTkFrame(self.charts_frame, fg_color=COLORS['bg_card'], corner_radius=8)
        card.pack(fill="x", pady=SPACING['sm'])

        ctk.CTkLabel(
            card,
            text="Tasks by Context",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['md'], SPACING['sm']))

        stats = self.task_manager.get_completion_stats_by_context()

        if not stats:
            ctk.CTkLabel(
                card,
                text="No completed tasks yet",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary']
            ).pack(pady=SPACING['md'])
            return

        context_colors = {
            "@Studio": "#9B59B6",
            "@Mixing": "#3498DB",
            "@Marketing": "#E74C3C",
            "@Admin": "#95A5A6",
            "@Other": "#7F8C8D"
        }

        total = sum(s['count'] for s in stats)

        for stat in stats:
            context = stat['context'] or '@Other'
            count = stat['count']
            percent = (count / total * 100) if total > 0 else 0
            color = context_colors.get(context, "#7F8C8D")

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=SPACING['lg'], pady=2)

            # Color dot
            dot = ctk.CTkFrame(row, fg_color=color, width=12, height=12, corner_radius=6)
            dot.pack(side="left", padx=(0, SPACING['sm']))

            ctk.CTkLabel(
                row,
                text=context,
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg'],
                width=100,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=f"{count} ({percent:.0f}%)",
                font=ctk.CTkFont(family="JetBrains Mono", size=12),
                text_color=COLORS['fg_secondary']
            ).pack(side="right")

        # Padding at bottom
        ctk.CTkFrame(card, fg_color="transparent", height=SPACING['md']).pack()
