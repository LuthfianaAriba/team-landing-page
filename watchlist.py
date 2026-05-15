import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from dashboardCinephile import NavBar

BG_MAIN  = "#1A1A1A"
BG_NAV   = "#111111"
BG_CARD  = "#2A2A2A"
ORANGE   = "#FF8C00"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#AAAAAA"
GREEN    = "#38a169"
BLUE     = "#3182ce"
RED      = "#c0392b"


class WatchlistPage(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.filter = "all"
        self.setStyleSheet(f"background: {BG_MAIN};")

        self.current_user = "guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json", "r") as f:
                    self.current_user = json.load(f).get("username", "guest")
        except: pass

        self.data_file = f"watchlist_{self.current_user}.json"
        self.watchlist_data = self._load_data()
        self._build_ui()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return []
        return []

    def _save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.watchlist_data, f, indent=4)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Navbar ──
        nav = QWidget()
        nav.setFixedHeight(50)
        nav.setStyleSheet(f"background: {BG_NAV};")
        nav_hl = QHBoxLayout(nav)
        nav_hl.setContentsMargins(10, 0, 20, 0)

        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setStyleSheet(f"color: {ORANGE}; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.app.show_page("dashboard"))
        nav_hl.addWidget(back_btn)

        title_lbl = QLabel(f"My Watchlist ({self.current_user})")
        title_lbl.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white; background: transparent;")
        nav_hl.addWidget(title_lbl)
        nav_hl.addStretch()

        for lbl, st in [("All", "all"), ("Plan to Watch", "Plan to Watch"), ("Watching", "Watching"), ("Watched", "Watched")]:
            btn = QPushButton(lbl)
            btn.setFixedSize(100, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"color: {ORANGE}; background: transparent; border: none; font-size: 11px; font-weight: bold;")
            btn.clicked.connect(lambda _, s=st: self._set_filter(s))
            nav_hl.addWidget(btn)

        main_layout.addWidget(nav)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        body = QWidget()
        body.setStyleSheet(f"background: {BG_MAIN};")
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(20, 20, 20, 20)
        self.body_layout.setSpacing(20)

        self._build_form()

        self.movie_area = QWidget()
        self.movie_area.setStyleSheet("background: transparent;")
        self.movie_area_layout = QVBoxLayout(self.movie_area)
        self.movie_area_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.addWidget(self.movie_area)
        self.body_layout.addStretch()

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self._refresh()

    def _build_form(self):
        form = QWidget()
        form.setStyleSheet(f"background: {BG_CARD}; border-radius: 10px;")
        fl = QVBoxLayout(form)
        fl.setContentsMargins(20, 15, 20, 15)

        form_title = QLabel("Add Custom Movie to Watchlist")
        form_title.setFont(QFont("Trebuchet MS", 16, QFont.Weight.Bold))
        form_title.setStyleSheet("color: white; background: transparent;")
        form_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(form_title)

        row = QHBoxLayout()
        self.e_title = QLineEdit()
        self.e_title.setPlaceholderText("Movie Title")
        self.e_title.setFixedSize(200, 36)
        self.e_title.setStyleSheet("background: #333; color: white; border-radius: 6px; padding: 0 8px; border: none;")

        self.e_year = QLineEdit()
        self.e_year.setPlaceholderText("Year")
        self.e_year.setFixedSize(70, 36)
        self.e_year.setStyleSheet("background: #333; color: white; border-radius: 6px; padding: 0 8px; border: none;")

        self.status_var = QComboBox()
        self.status_var.addItems(["Plan to Watch", "Watching", "Watched"])
        self.status_var.setFixedSize(130, 36)
        self.status_var.setStyleSheet(f"""
            QComboBox {{ background: {ORANGE}; color: black; border-radius: 6px;
                         font-weight: bold; font-size: 12px; padding: 0 8px; border: none; }}
            QComboBox QAbstractItemView {{ background: #333; color: white; }}
        """)

        add_btn = QPushButton("Add")
        add_btn.setFixedSize(60, 36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"background: {GREEN}; color: white; border-radius: 6px; font-weight: bold; border: none;")
        add_btn.clicked.connect(self._add_movie)

        for w in [self.e_title, self.e_year, self.status_var, add_btn]:
            row.addWidget(w)
        row.addStretch()
        fl.addLayout(row)
        self.body_layout.addWidget(form)

    def _refresh(self):
        self.watchlist_data = self._load_data()
        while self.movie_area_layout.count():
            item = self.movie_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = [m for m in self.watchlist_data if self.filter == "all" or m.get("status") == self.filter]
        if not filtered:
            empty = QLabel("Your watchlist is empty.")
            empty.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movie_area_layout.addWidget(empty)
            return

        row_widget = None
        row_layout = None
        for i, movie in enumerate(filtered):
            if i % 3 == 0:
                row_widget = QWidget()
                row_widget.setStyleSheet("background: transparent;")
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)
                self.movie_area_layout.addWidget(row_widget)
            self._render_card(row_layout, movie)

        # Fill empty slots in last row
        remainder = len(filtered) % 3
        if remainder != 0 and row_layout:
            for _ in range(3 - remainder):
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                row_layout.addWidget(spacer)

    def _render_card(self, parent_layout, movie):
        card = QWidget()
        card.setFixedSize(280, 130)
        card.setStyleSheet(f"background: {BG_CARD}; border-radius: 10px;")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(15, 15, 15, 15)

        title = movie.get("title", "Unknown")
        t_lbl = QLabel(title[:25] + "..." if len(title) > 25 else title)
        t_lbl.setFont(QFont("Helvetica", 15, QFont.Weight.Bold))
        t_lbl.setStyleSheet("color: white; background: transparent;")
        cl.addWidget(t_lbl)

        y_lbl = QLabel(movie.get("year", "N/A"))
        y_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 12px; background: transparent;")
        cl.addWidget(y_lbl)
        cl.addStretch()

        action_row = QHBoxLayout()
        current_status = movie.get("status", "Plan to Watch")
        btn_color = GREEN if current_status == "Watched" else (BLUE if current_status == "Watching" else "#555")

        status_menu = QComboBox()
        status_menu.addItems(["Plan to Watch", "Watching", "Watched"])
        status_menu.setCurrentText(current_status)
        status_menu.setFixedSize(120, 26)
        status_menu.setStyleSheet(f"""
            QComboBox {{ background: {btn_color}; color: white; border-radius: 4px;
                         font-size: 11px; padding: 0 6px; border: none; }}
            QComboBox QAbstractItemView {{ background: #333; color: white; }}
        """)
        status_menu.currentTextChanged.connect(lambda v, m=movie: self._update_status(m, v))

        del_btn = QPushButton("Delete")
        del_btn.setFixedSize(55, 26)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"background: {RED}; color: white; border-radius: 4px; font-size: 11px; border: none;")
        del_btn.clicked.connect(lambda _, m=movie: self._delete_movie(m))

        action_row.addWidget(status_menu)
        action_row.addStretch()
        action_row.addWidget(del_btn)
        cl.addLayout(action_row)

        parent_layout.addWidget(card)

    def _update_status(self, movie, new_status):
        movie["status"] = new_status
        self._save_data()
        self._refresh()

    def _add_movie(self):
        title = self.e_title.text().strip()
        if not title:
            return
        self.watchlist_data.insert(0, {
            "title": title,
            "year": self.e_year.text().strip() or "Unknown",
            "genre": "N/A", "rating": "N/A",
            "status": self.status_var.currentText()
        })
        self._save_data()
        self.e_title.clear()
        self.e_year.clear()
        self._refresh()

    def _delete_movie(self, movie):
        reply = QMessageBox.question(self, "Delete", f'Remove "{movie.get("title")}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.watchlist_data.remove(movie)
            self._save_data()
            self._refresh()

    def _set_filter(self, status):
        self.filter = status
        self._refresh()