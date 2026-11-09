"""
AIRCTRL Quick Launch Page
Interactive bookmark cards for favorite tools & AI assistants with usage statistics,
browser integration, pinning, and add/edit/delete dialogues.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QDialog, QLineEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from core.quick_launcher import launcher
from utils.helpers import play_feedback_sound

WEBSITE_PALETTES = {
    "youtube": {"bg": "rgba(255, 0, 0, 0.15)", "border": "#ff0033", "color": "#ff4d4d", "icon": "▶"},
    "googledocs": {"bg": "rgba(66, 133, 244, 0.15)", "border": "#4285f4", "color": "#6ba4ff", "icon": "📄"},
    "chatgpt": {"bg": "rgba(16, 163, 127, 0.15)", "border": "#10a37f", "color": "#1ddba8", "icon": "🤖"},
    "claude": {"bg": "rgba(217, 119, 87, 0.15)", "border": "#d97757", "color": "#f59e7a", "icon": "🧠"},
    "github": {"bg": "rgba(148, 163, 184, 0.15)", "border": "#94a3b8", "color": "#f1f5f9", "icon": "🐙"}
}

class AddEditWebsiteDialog(QDialog):
    """Dialog to create or edit Quick Launch websites."""
    def __init__(self, site_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Website" if site_data else "Add New Website")
        self.setFixedSize(380, 260)
        self.site_data = site_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.in_name = QLineEdit(self)
        self.in_name.setPlaceholderText("Website Name (e.g. Reddit)")
        if site_data:
            self.in_name.setText(site_data.get("name", ""))

        self.in_url = QLineEdit(self)
        self.in_url.setPlaceholderText("URL (e.g. https://reddit.com)")
        if site_data:
            self.in_url.setText(site_data.get("url", ""))

        self.in_shortcut = QLineEdit(self)
        self.in_shortcut.setPlaceholderText("Shortcut Key (e.g. R)")
        self.in_shortcut.setMaxLength(1)
        if site_data:
            self.in_shortcut.setText(site_data.get("shortcut", ""))

        self.chk_pin = QCheckBox("Pin to top of list")
        if site_data:
            self.chk_pin.setChecked(site_data.get("pinned", False))

        layout.addWidget(QLabel("Website Title:"))
        layout.addWidget(self.in_name)
        layout.addWidget(QLabel("Destination URL:"))
        layout.addWidget(self.in_url)
        layout.addWidget(QLabel("Gesture Shortcut Letter:"))
        layout.addWidget(self.in_shortcut)
        layout.addWidget(self.chk_pin)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save Website")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)


class QuickLaunchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        launcher.sites_updated.connect(self._render_sites)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        top_box = QHBoxLayout()
        header = QVBoxLayout()
        t = QLabel("QUICK WEBSITE LAUNCHER")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Launch popular platforms and AI tools instantly without touching the keyboard.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header.addWidget(t)
        header.addWidget(sub)
        top_box.addLayout(header)
        top_box.addStretch()

        btn_add = QPushButton("+ Add Custom Website")
        btn_add.setProperty("class", "PrimaryBtn")
        btn_add.clicked.connect(self._on_add_site)
        top_box.addWidget(btn_add)

        main_layout.addLayout(top_box)

        # Scroll Area for Website Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(16)
        scroll.setWidget(self.container)

        main_layout.addWidget(scroll)
        self._render_sites()

    def _render_sites(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sites = launcher.get_sites(sorted_by_usage=True)
        cols = 3

        for idx, site in enumerate(sites):
            row = idx // cols
            col = idx % cols
            card = self._create_site_card(site)
            self.grid_layout.addWidget(card, row, col)

    def _create_site_card(self, site: dict) -> QFrame:
        sid = site.get("id", "")
        name = site.get("name", "Website")
        url = site.get("url", "")
        count = site.get("usage_count", 0)
        last_opened = site.get("last_opened") or "Never"
        shortcut = site.get("shortcut", "")
        pinned = site.get("pinned", False)

        pal = WEBSITE_PALETTES.get(sid, {
            "bg": "rgba(0, 242, 254, 0.12)",
            "border": "#00f2fe",
            "color": "#00f2fe",
            "icon": "🌐"
        })

        card = QFrame()
        card.setProperty("class", "Card")
        card.setStyleSheet(f"""
            QFrame.Card {{
                background-color: #121c2d;
                border: 1px solid {pal['border']};
                border-radius: 12px;
            }}
            QFrame.Card:hover {{
                background-color: #16243a;
                border: 2px solid {pal['border']};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Top Bar: Icon + Title + Pin
        top = QHBoxLayout()
        icon_lbl = QLabel(pal["icon"])
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {pal['color']};")

        title_box = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700;")
        url_lbl = QLabel(url.replace("https://", "").replace("http://", ""))
        url_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        title_box.addWidget(name_lbl)
        title_box.addWidget(url_lbl)

        btn_pin = QPushButton("📌" if pinned else "📍")
        btn_pin.setToolTip("Toggle Pin")
        btn_pin.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        btn_pin.clicked.connect(lambda ch=False, s=sid: launcher.toggle_pin(s))

        top.addWidget(icon_lbl)
        top.addLayout(title_box, stretch=1)
        top.addWidget(btn_pin)
        layout.addLayout(top)

        # Metadata Row
        meta = QHBoxLayout()
        lbl_count = QLabel(f"Opened: {count} times")
        lbl_count.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600;")
        lbl_last = QLabel(f"Last: {last_opened.split(' ')[0] if ' ' in str(last_opened) else last_opened}")
        lbl_last.setStyleSheet("color: #94a3b8; font-size: 11px;")
        meta.addWidget(lbl_count)
        meta.addStretch()
        meta.addWidget(lbl_last)
        layout.addLayout(meta)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_open = QPushButton("Open in Browser")
        btn_open.setProperty("class", "PrimaryBtn")
        btn_open.clicked.connect(lambda ch=False, s=sid: launcher.launch(s))

        btn_edit = QPushButton("Edit")
        btn_edit.setProperty("class", "SecondaryBtn")
        btn_edit.clicked.connect(lambda ch=False, s=site: self._on_edit_site(s))

        btn_del = QPushButton("✕")
        btn_del.setToolTip("Remove Website")
        btn_del.setProperty("class", "DangerBtn")
        btn_del.clicked.connect(lambda ch=False, s=sid: self._on_delete_site(s))

        btn_row.addWidget(btn_open, stretch=2)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        return card

    def _on_add_site(self):
        dlg = AddEditWebsiteDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.in_name.text()
            url = dlg.in_url.text()
            sc = dlg.in_shortcut.text()
            pinned = dlg.chk_pin.isChecked()
            if name and url:
                launcher.add_site(name, url, shortcut=sc, pinned=pinned)

    def _on_edit_site(self, site: dict):
        dlg = AddEditWebsiteDialog(site_data=site, parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.in_name.text()
            url = dlg.in_url.text()
            sc = dlg.in_shortcut.text()
            pinned = dlg.chk_pin.isChecked()
            launcher.edit_site(site["id"], name, url, shortcut=sc, pinned=pinned)

    def _on_delete_site(self, site_id: str):
        reply = QMessageBox.question(
            self, "Confirm Removal", "Are you sure you want to remove this website shortcut?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            launcher.remove_site(site_id)

