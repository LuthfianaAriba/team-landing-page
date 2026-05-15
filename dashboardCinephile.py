import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QGridLayout, QSizePolicy, QMenu
)
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PIL import Image, ImageOps
import io

BG_MAIN    = "#1A1A1A"
BG_NAV     = "#111111"
BG_TAB     = "#2E2E2E"
ACCENT     = "#E53935"
ORANGE     = "#FF8C00"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#AAAAAA"


def pil_to_qpixmap(pil_img, size=None):
    if size:
        try:
            pil_img = ImageOps.fit(pil_img, size, Image.LANCZOS)
        except:
            pil_img = pil_img.resize(size, Image.LANCZOS)
    pil_img = pil_img.convert("RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    qimg = QImage.fromData(buf.getvalue())
    return QPixmap.fromImage(qimg)


class NavBar(QWidget):
    def __init__(self, app, current_page="dashboard"):
        super().__init__()
        self.app = app
        self.setFixedHeight(60)
        self.setStyleSheet(f"background: {BG_NAV};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # ── Kiri: avatar + username ──
        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json") as f:
                    self.username = json.load(f).get("username", "Guest")
        except: pass

        initial = self.username[0].upper()
        avatar = QLabel(initial)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {ACCENT}; color: white;
            border-radius: 18px; font-weight: bold; font-size: 15px;
        """)

        user_lbl = QPushButton(f"  {self.username} ▼")
        user_lbl.setStyleSheet("color: white; background: transparent; border: none; font-size: 13px; font-weight: bold;")
        user_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        user_lbl.clicked.connect(self._show_profile_menu)

        left_w = QWidget()
        left_w.setFixedWidth(250)
        left_w.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_w)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_layout.addWidget(avatar)
        left_layout.addWidget(user_lbl)
        left_layout.addStretch()

        # ── Tengah: pill nav ──
        pill = QWidget()
        pill.setFixedHeight(34)
        pill.setStyleSheet("background: #2E2E2E; border-radius: 17px;")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(6, 3, 6, 3)
        pill_layout.setSpacing(2)

        nav_items = [
            ("Home",           "dashboard",    70),
            ("Genre Analysis", "genreanalyze", 110),
            ("Movie Table",    "movietable",   92),
            ("Watchlist",      "watchlist",    80),
        ]
        for text, page, w in nav_items:
            active = (page == current_page)
            btn = QPushButton(text)
            btn.setFixedSize(w, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#E53935' if active else 'transparent'};
                    color: {'white' if active else '#AAAAAA'};
                    border-radius: 14px;
                    font-size: 11px; font-weight: bold;
                    border: none;
                }}
                QPushButton:hover {{ background: {'#C62828' if active else '#3A3A3A'}; color: white; }}
            """)
            btn.clicked.connect(lambda _, p=page: self.app.show_page(p))
            pill_layout.addWidget(btn)

        # ── Kanan: search ──
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search Local Database...")
        self.search_entry.setFixedSize(200, 32)
        self.search_entry.setStyleSheet("""
            QLineEdit { background: #222; border: 1px solid #444; border-radius: 6px;
                        color: white; font-size: 12px; padding: 0 8px; }
            QLineEdit:focus { border-color: #E53935; }
        """)
        self.search_entry.returnPressed.connect(self._do_search)

        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(40, 32)
        search_btn.setStyleSheet("background: #E53935; border-radius: 6px; color: white; font-size: 14px; border: none;")
        search_btn.clicked.connect(self._do_search)

        right_w = QWidget()
        right_w.setFixedWidth(250)
        right_w.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_w)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_layout.addStretch()
        right_layout.addWidget(self.search_entry)
        right_layout.addWidget(search_btn)

        layout.addWidget(left_w)
        layout.addStretch()
        layout.addWidget(pill)
        layout.addStretch()
        layout.addWidget(right_w)

    def _do_search(self):
        self.app.handle_local_search(self.search_entry.text())

    def _show_profile_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1E1E1E; border: 1px solid #333; border-radius: 8px; color: white; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background: #2A2A2A; }
        """)
        menu.addAction(f"Hello, {self.username}!")
        menu.addSeparator()
        logout_action = menu.addAction("Logout")
        logout_action.triggered.connect(self._logout)
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def _logout(self):
        if os.path.exists("session.json"):
            os.remove("session.json")
        self.app.show_page("login")


class DashboardPage(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setStyleSheet(f"background: {BG_MAIN};")

        if not hasattr(self.app, '_img_cache'):
            self.app._img_cache = {}

        self._hero_pixmaps = []
        self._current_hero = 0
        self._carousel_timer = QTimer(self)
        self._carousel_timer.timeout.connect(self._next_hero)

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(NavBar(self.app, "dashboard"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet(f"background: {BG_MAIN};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._build_hero(content_layout)
        self._build_movie_list(content_layout)
        self._build_tagline(content_layout)
        self._build_watchlist_banner(content_layout)
        self._build_footer(content_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_hero(self, layout):
        self.hero_label = QLabel()
        self.hero_label.setFixedHeight(450)
        self.hero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hero_label.setStyleSheet("background: #2A2A2A;")
        self.hero_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        hero_files = ["hero1.jpeg", "hero2.jpeg", "hero3.jpeg"]
        base = os.path.dirname(os.path.abspath(__file__))
        for f in hero_files:
            path = os.path.join(base, f)
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGB")
                    # Simpan pixmap resolusi asli tanpa resize paksa
                    px = pil_to_qpixmap(img)
                    self._hero_pixmaps.append(px)
                except: pass

        if self._hero_pixmaps:
            self._carousel_timer.start(3000)
            QTimer.singleShot(0, self._refresh_hero)

        layout.addWidget(self.hero_label)

    def _refresh_hero(self):
        if not self._hero_pixmaps:
            return
        w = self.hero_label.width() or self.width() or 1100
        h = 450
        px = self._hero_pixmaps[self._current_hero]

        # Scale gambar: fit ke dalam kotak w x h tanpa crop, pakai KeepAspectRatio
        # Lalu padding kiri-kanan dengan background gelap otomatis via AlignCenter
        scaled = px.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Kalau mau full width tanpa letterbox, pakai KeepAspectRatioByExpanding
        # tapi crop vertikal (bukan horizontal) dengan crop center
        if scaled.width() < w:
            # Gambar terlalu kecil horizontal → expand by width, crop vertikal
            scaled = px.scaled(
                w, 99999,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if scaled.height() > h:
                # Crop tengah vertikal
                y_off = (scaled.height() - h) // 2
                scaled = scaled.copy(0, y_off, w, h)

        self.hero_label.setPixmap(scaled)

    def _next_hero(self):
        if not self._hero_pixmaps:
            return
        self._current_hero = (self._current_hero + 1) % len(self._hero_pixmaps)
        self._refresh_hero()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_hero()

    def _build_movie_list(self, layout):
        container = QWidget()
        container.setStyleSheet("background: #F4F4F4; border-radius: 10px;")
        vl = QVBoxLayout(container)
        vl.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Top 10\nMovies")
        title.setFont(QFont("Helvetica", 50, QFont.Weight.Bold))
        title.setStyleSheet("color: #111111; background: transparent;")
        vl.addWidget(title)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 10, 0, 5)
        for text, w in [("Film", 240), ("Year", 60), ("Mood", 160), ("Synopsis", 0)]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #AAAAAA; font-size: 12px; font-weight: bold; background: transparent;")
            if w:
                lbl.setFixedWidth(w)
            else:
                lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            hl.addWidget(lbl)
        vl.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background: #DDDDDD;")
        vl.addWidget(sep)

        movies = self.app.movie_list[:10]
        for movie in movies:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 8, 0, 8)

            def make_lbl(text, color, w=None, wrap=None):
                l = QLabel(text)
                l.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;")
                if w: l.setFixedWidth(w)
                if wrap: l.setWordWrap(True)
                return l

            title_lbl = make_lbl(movie.get("title", "Unknown"), "#7A1C1C", 240, True)
            year_lbl  = make_lbl(str(movie.get("year", "N/A")).replace("1'",""), "#111111", 60)
            mood_lbl  = make_lbl(movie.get("genre", "N/A"), "#2A368F", 160, True)
            syn_text  = movie.get("description", movie.get("synopsis", ""))
            if len(syn_text) > 130: syn_text = syn_text[:127] + "..."
            syn_lbl   = make_lbl(syn_text, "#8A4B1A")
            syn_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            syn_lbl.setWordWrap(True)

            for w in [title_lbl, year_lbl, mood_lbl, syn_lbl]:
                rl.addWidget(w)

            def go(e, m=movie):
                self.app.show_page("moviedetail", m)

            for w in [row, title_lbl, year_lbl, mood_lbl, syn_lbl]:
                w.mousePressEvent = go

            vl.addWidget(row)

            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background: #DDDDDD;")
            vl.addWidget(div)

        layout.addWidget(container)

    def _build_tagline(self, layout):
        tl = QLabel("a passionate enthusiast — a passionate enthusiast — a passionate")
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.setFixedHeight(100)
        tl.setStyleSheet(f"color: white; font-size: 22px; font-style: italic; background: {BG_MAIN};")
        layout.addWidget(tl)

    def _build_watchlist_banner(self, layout):
        banner = QWidget()
        banner.setFixedHeight(200)
        banner.setStyleSheet("background: #FF8C00;")
        bl = QVBoxLayout(banner)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h = QLabel("Don't forget your watchlist!")
        h.setFont(QFont("Georgia", 28))
        h.setStyleSheet("color: #111111; font-style: italic; background: transparent;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Update it and discover what to watch next.")
        sub.setStyleSheet("color: #222222; font-size: 14px; font-weight: bold; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Go to Watchlist")
        btn.setFixedSize(160, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background: #111111; color: white; border-radius: 0; font-size: 12px; font-weight: bold; border: none;")
        btn.clicked.connect(lambda: self.app.show_page("watchlist"))

        bl.addWidget(h)
        bl.addWidget(sub)
        bl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

    def _build_footer(self, layout):
        footer = QWidget()
        footer.setFixedHeight(170)
        footer.setStyleSheet("background: #0A0A0A;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(40, 0, 40, 0)

        left = QLabel("Cinephile")
        left.setFont(QFont("Helvetica", 50, QFont.Weight.Bold))
        left.setStyleSheet("color: white; background: transparent;")

        right = QLabel("©2026 Movie Archive\nWords, images, and signals from the edge")
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        right.setStyleSheet("color: #AAAAAA; font-size: 10px; background: transparent;")

        fl.addWidget(left)
        fl.addStretch()
        fl.addWidget(right)
        layout.addWidget(footer)

    def closeEvent(self, event):
        self._carousel_timer.stop()
        super().closeEvent(event)
        
