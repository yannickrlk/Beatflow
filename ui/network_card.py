"""Network Card component for ProducerOS - Premium card display for contacts."""

import os
import customtkinter as ctk
from PIL import Image
from ui.theme import COLORS, SPACING
from core.client_manager import ClientManager

# Role color mapping for badges
ROLE_COLORS = {
    'Producer': '#8B5CF6',    # Purple
    'Artist': '#EC4899',      # Pink
}

# Load Instagram logo - invert to white on transparent for dark UI
_INSTAGRAM_LOGO = None
def _get_instagram_logo():
    global _INSTAGRAM_LOGO
    if _INSTAGRAM_LOGO is None:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'IMAGE', 'instagram_logo.jpg')
        if os.path.exists(logo_path):
            img = Image.open(logo_path).convert('RGBA')
            data = img.getdata()
            new_data = []
            for pixel in data:
                # Black/dark pixels -> white, white/light pixels -> transparent
                brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
                if brightness > 200:  # Light/white -> transparent
                    new_data.append((0, 0, 0, 0))
                else:  # Dark/black -> white
                    new_data.append((255, 255, 255, 255))
            img.putdata(new_data)
            _INSTAGRAM_LOGO = ctk.CTkImage(light_image=img, dark_image=img, size=(16, 16))
    return _INSTAGRAM_LOGO

# Load Twitter/X logo - make black background transparent, keep white X
_TWITTER_LOGO = None
def _get_twitter_logo():
    global _TWITTER_LOGO
    if _TWITTER_LOGO is None:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'IMAGE', 'twitter_logo.png')
        if os.path.exists(logo_path):
            img = Image.open(logo_path).convert('RGBA')
            data = img.getdata()
            new_data = []
            for pixel in data:
                # Black/dark pixels -> transparent, white/light pixels -> keep white
                brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
                if brightness < 50:  # Dark/black -> transparent
                    new_data.append((0, 0, 0, 0))
                else:  # Light/white -> keep white
                    new_data.append((255, 255, 255, 255))
            img.putdata(new_data)
            _TWITTER_LOGO = ctk.CTkImage(light_image=img, dark_image=img, size=(16, 16))
    return _TWITTER_LOGO


class ClientCard(ctk.CTkFrame):
    """A premium card displaying contact information with social links and role badge."""

    def __init__(self, parent, client: dict, on_click=None, on_edit=None, on_delete=None, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border'],
            **kwargs
        )

        self.client = client
        self.on_click = on_click
        self.on_edit = on_edit
        self.on_delete = on_delete

        self._build_ui()
        self._bind_hover()

    def _build_ui(self):
        """Build the card UI."""
        # Main content padding
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['md'])

        # Header row with name and role badge
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, SPACING['sm']))

        # Name (large, bold)
        name_label = ctk.CTkLabel(
            header_frame,
            text=self.client.get('name', 'Unknown'),
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        name_label.pack(side="left")

        # Role badge
        role = self.client.get('role', 'Producer')
        role_color = ROLE_COLORS.get(role, ROLE_COLORS['Producer'])
        role_badge = ctk.CTkLabel(
            header_frame,
            text=role,
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color="#ffffff",
            fg_color=role_color,
            corner_radius=4,
            padx=6,
            pady=2
        )
        role_badge.pack(side="right")

        # Contact info section
        contact_frame = ctk.CTkFrame(content, fg_color="transparent")
        contact_frame.pack(fill="x", pady=(0, SPACING['sm']))

        # Email (if available)
        if self.client.get('email'):
            self._create_info_row(contact_frame, "\u2709", self.client['email'])  # Envelope icon

        # Phone (if available)
        if self.client.get('phone'):
            self._create_info_row(contact_frame, "\u260E", self.client['phone'])  # Phone icon

        # Social links row
        socials_frame = ctk.CTkFrame(content, fg_color="transparent")
        socials_frame.pack(fill="x", pady=(SPACING['xs'], 0))

        # Instagram button with real logo
        if self.client.get('instagram'):
            ig_logo = _get_instagram_logo()
            ig_btn = ctk.CTkButton(
                socials_frame,
                text="" if ig_logo else "\u25CE",
                image=ig_logo,
                font=ctk.CTkFont(size=16),
                fg_color=COLORS['bg_hover'],
                hover_color="#E1306C",
                width=32,
                height=28,
                corner_radius=6,
                text_color=COLORS['fg'],
                command=lambda: self._open_social('instagram', self.client['instagram'])
            )
            ig_btn.pack(side="left", padx=(0, SPACING['xs']))

        # Twitter/X button with real logo
        if self.client.get('twitter'):
            tw_logo = _get_twitter_logo()
            tw_btn = ctk.CTkButton(
                socials_frame,
                text="" if tw_logo else "\u2573",
                image=tw_logo,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['bg_hover'],
                hover_color="#000000",  # X black
                width=32,
                height=28,
                corner_radius=6,
                text_color=COLORS['fg'],
                command=lambda: self._open_social('twitter', self.client['twitter'])
            )
            tw_btn.pack(side="left", padx=(0, SPACING['xs']))

        # Website button
        if self.client.get('website'):
            web_btn = ctk.CTkButton(
                socials_frame,
                text="\u2197",  # Arrow icon for external link
                font=ctk.CTkFont(size=14),
                fg_color=COLORS['bg_hover'],
                hover_color=COLORS['accent'],
                width=36,
                height=28,
                corner_radius=6,
                text_color=COLORS['fg'],
                command=lambda: self._open_social('website', self.client['website'])
            )
            web_btn.pack(side="left", padx=(0, SPACING['xs']))

        # Edit button (right side)
        edit_btn = ctk.CTkButton(
            socials_frame,
            text="\u270E",  # Pencil icon
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=28,
            height=28,
            corner_radius=6,
            text_color=COLORS['fg_dim'],
            command=self._on_edit_click
        )
        edit_btn.pack(side="right")

        # Notes preview (if available, truncated)
        if self.client.get('notes'):
            notes_text = self.client['notes'][:50] + "..." if len(self.client['notes']) > 50 else self.client['notes']
            notes_label = ctk.CTkLabel(
                content,
                text=notes_text,
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_dim'],
                anchor="w",
                wraplength=200
            )
            notes_label.pack(fill="x", pady=(SPACING['sm'], 0))

    def _create_info_row(self, parent, icon: str, text: str):
        """Create a row with icon and text."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        icon_label = ctk.CTkLabel(
            row,
            text=icon,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_dim'],
            width=20
        )
        icon_label.pack(side="left")

        text_label = ctk.CTkLabel(
            row,
            text=text,
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        text_label.pack(side="left", fill="x", expand=True)

    def _bind_hover(self):
        """Bind hover effects."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter."""
        self.configure(border_color=COLORS['accent'])

    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(border_color=COLORS['border'])

    def _open_social(self, platform: str, handle: str):
        """Open a social link."""
        ClientManager.open_social_link(platform, handle)

    def _on_edit_click(self):
        """Handle edit button click."""
        if self.on_edit:
            self.on_edit(self.client)


class ClientListRow(ctk.CTkFrame):
    """A row for list view display of a contact with role badge."""

    def __init__(self, parent, client: dict, on_edit=None, on_delete=None, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=4,
            height=48,
            **kwargs
        )
        self.pack_propagate(False)

        self.client = client
        self.on_edit = on_edit
        self.on_delete = on_delete

        self._build_ui()
        self._bind_hover()

    def _build_ui(self):
        """Build the row UI."""
        # Name column (flex)
        name_label = ctk.CTkLabel(
            self,
            text=self.client.get('name', 'Unknown'),
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w",
            width=140
        )
        name_label.pack(side="left", padx=SPACING['md'], pady=SPACING['sm'])

        # Role badge (compact)
        role = self.client.get('role', 'Producer')
        role_color = ROLE_COLORS.get(role, ROLE_COLORS['Producer'])
        role_badge = ctk.CTkLabel(
            self,
            text=role,
            font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
            text_color="#ffffff",
            fg_color=role_color,
            corner_radius=3,
            padx=4,
            pady=1,
            width=60
        )
        role_badge.pack(side="left", padx=(0, SPACING['sm']))

        # Email column
        email_label = ctk.CTkLabel(
            self,
            text=self.client.get('email', '-'),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w",
            width=200
        )
        email_label.pack(side="left", padx=SPACING['sm'])

        # Phone column
        phone_label = ctk.CTkLabel(
            self,
            text=self.client.get('phone', '-'),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w",
            width=120
        )
        phone_label.pack(side="left", padx=SPACING['sm'])

        # Social buttons (right side)
        socials_frame = ctk.CTkFrame(self, fg_color="transparent")
        socials_frame.pack(side="right", padx=SPACING['md'])

        # Instagram with real logo
        if self.client.get('instagram'):
            ig_logo = _get_instagram_logo()
            ig_btn = ctk.CTkButton(
                socials_frame,
                text="" if ig_logo else "\u25CE",
                image=ig_logo,
                font=ctk.CTkFont(size=14),
                fg_color=COLORS['bg_hover'],
                hover_color="#E1306C",
                width=28,
                height=24,
                corner_radius=4,
                text_color=COLORS['fg'],
                command=lambda: ClientManager.open_social_link('instagram', self.client['instagram'])
            )
            ig_btn.pack(side="left", padx=2)

        # Twitter with real logo
        if self.client.get('twitter'):
            tw_logo = _get_twitter_logo()
            tw_btn = ctk.CTkButton(
                socials_frame,
                text="" if tw_logo else "\u2573",
                image=tw_logo,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=COLORS['bg_hover'],
                hover_color="#000000",
                width=28,
                height=24,
                corner_radius=4,
                text_color=COLORS['fg'],
                command=lambda: ClientManager.open_social_link('twitter', self.client['twitter'])
            )
            tw_btn.pack(side="left", padx=2)

        # Website
        if self.client.get('website'):
            web_btn = ctk.CTkButton(
                socials_frame,
                text="\u2197",
                font=ctk.CTkFont(size=12),
                fg_color=COLORS['bg_hover'],
                hover_color=COLORS['accent'],
                width=32,
                height=24,
                corner_radius=4,
                text_color=COLORS['fg'],
                command=lambda: ClientManager.open_social_link('website', self.client['website'])
            )
            web_btn.pack(side="left", padx=2)

        # Edit button
        edit_btn = ctk.CTkButton(
            socials_frame,
            text="\u270E",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=28,
            height=24,
            corner_radius=4,
            text_color=COLORS['fg_dim'],
            command=self._on_edit_click
        )
        edit_btn.pack(side="left", padx=(SPACING['sm'], 0))

    def _bind_hover(self):
        """Bind hover effects."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter."""
        self.configure(fg_color=COLORS['bg_hover'])

    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(fg_color=COLORS['bg_card'])

    def _on_edit_click(self):
        """Handle edit button click."""
        if self.on_edit:
            self.on_edit(self.client)
