import os
import json
import random
import io
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QMenu
)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from PIL import Image, ImageOps

BG_MAIN    = "#1A1A1A"
BG_NAV     = "#111111"
BG_TAB     = "#2E2E2E"
ACCENT     = "#E53935"
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
    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))


class NavBar(QWidget):
    def __init__(self, app, current_page="dashboard"):
        super().__init__()
        self.app = app
        self.setFixedHeight(60)
        self.setStyleSheet(f"background: {BG_NAV};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json") as f:
                    self.username = json.load(f).get("username", "Guest")
        except: pass

        # ── Kiri ──
        avatar = QLabel(self.username[0].upper())
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"background: {ACCENT}; color: white; border-radius: 18px; font-weight: bold; font-size: 15px;")

        user_lbl = QPushButton(f"  {self.username} ▼")
        user_lbl.setStyleSheet("color: white; background: transparent; border: none; font-size: 13px; font-weight: bold;")
        user_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        user_lbl.clicked.connect(self._show_profile_menu)

        left_w = QWidget()
        left_w.setFixedWidth(250)
        left_w.setStyleSheet("background: transparent;")
        ll = QHBoxLayout(left_w)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(4)
        ll.addWidget(avatar)
        ll.addWidget(user_lbl)
        ll.addStretch()

        # ── Pill ──
        pill = QWidget()
        pill.setFixedHeight(34)
        pill.setStyleSheet("background: #2E2E2E; border-radius: 17px;")
        pl = QHBoxLayout(pill)
        pl.setContentsMargins(6, 3, 6, 3)
        pl.setSpacing(2)

        for text, page, w in [
            ("Home", "dashboard", 70),
            ("Genre Analysis", "genreanalyze", 110),
            ("Movie Table", "movietable", 92),
            ("Watchlist", "watchlist", 80),
        ]:
            active = (page == current_page)
            btn = QPushButton(text)
            btn.setFixedSize(w, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#E53935' if active else 'transparent'};
                    color: {'white' if active else '#AAAAAA'};
                    border-radius: 14px; font-size: 11px; font-weight: bold; border: none;
                }}
                QPushButton:hover {{ background: {'#C62828' if active else '#3A3A3A'}; color: white; }}
            """)
            btn.clicked.connect(lambda _, p=page: self.app.show_page(p))
            pl.addWidget(btn)

        # ── Kanan ──
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search movie...")
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
        rl = QHBoxLayout(right_w)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(5)
        rl.addStretch()
        rl.addWidget(self.search_entry)
        rl.addWidget(search_btn)

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
        menu.addAction("Logout").triggered.connect(self._logout)
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
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        self._build_hero(cl)
        self._build_insights(cl)
        self._build_trending(cl)
        self._build_top10(cl)
        self._build_tagline(cl)
        self._build_watchlist_banner(cl)
        self._build_footer(cl)
        cl.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ── HERO ──────────────────────────────────────────────────────────────
    def _build_hero(self, layout):
        self.hero_label = QLabel()
        self.hero_label.setFixedHeight(400)
        self.hero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hero_label.setStyleSheet("background: #222222;")
        self.hero_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        base = os.path.dirname(os.path.abspath(__file__))
        for name in ["hero1.jpeg", "hero2.jpeg", "hero3.jpeg"]:
            path = os.path.join(base, name)
            if not os.path.exists(path):
                path = name
            if os.path.exists(path):
                try:
                    self._hero_pixmaps.append(pil_to_qpixmap(Image.open(path).convert("RGB")))
                except: pass

        if self._hero_pixmaps:
            self._carousel_timer.start(5000)
            QTimer.singleShot(0, self._refresh_hero)

        layout.addWidget(self.hero_label)

    def _refresh_hero(self):
        if not self._hero_pixmaps:
            return
        w = self.hero_label.width() or self.width() or 1100
        h = 400
        px = self._hero_pixmaps[self._current_hero]
        scaled = px.scaled(w, 99999, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if scaled.height() > h:
            y = (scaled.height() - h) // 2
            scaled = scaled.copy(0, y, w, h)
        self.hero_label.setPixmap(scaled)

    def _next_hero(self):
        if not self._hero_pixmaps:
            return
        self._current_hero = (self._current_hero + 1) % len(self._hero_pixmaps)
        self._refresh_hero()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_hero()

    # ── INSIGHTS ──────────────────────────────────────────────────────────
    def _build_insights(self, layout):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(40, 30, 40, 10)

        title = QLabel("Cinephile Insights")
        title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        wl.addWidget(title)

        cards_w = QWidget()
        cards_w.setStyleSheet("background: transparent;")
        cl = QHBoxLayout(cards_w)
        cl.setContentsMargins(0, 15, 0, 0)
        cl.setSpacing(10)

        for label, val, icon, color in [
            ("Total Movies", "250 Titles", "🎬", "#2d5a27"),
            ("Trending Genre", "Action/Sci-Fi", "🔥", "#2A368F"),
            ("Global Rating", "4.9/5.0", "⭐", "#8A4B1A"),
        ]:
            card = QWidget()
            card.setFixedHeight(100)
            card.setStyleSheet(f"background: {color}; border-radius: 15px;")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_l = QHBoxLayout(card)
            card_l.setContentsMargins(20, 0, 20, 0)

            ico_lbl = QLabel(icon)
            ico_lbl.setFont(QFont("Arial", 32))
            ico_lbl.setStyleSheet("background: transparent;")

            info = QWidget()
            info.setStyleSheet("background: transparent;")
            il = QVBoxLayout(info)
            il.setContentsMargins(10, 0, 0, 0)
            il.setSpacing(2)
            l1 = QLabel(label)
            l1.setStyleSheet("color: #DDD; font-size: 13px; background: transparent;")
            l2 = QLabel(val)
            l2.setFont(QFont("Arial Black", 18, QFont.Weight.Bold))
            l2.setStyleSheet("color: white; background: transparent;")
            il.addWidget(l1)
            il.addWidget(l2)

            card_l.addWidget(ico_lbl)
            card_l.addWidget(info)
            card_l.addStretch()
            cl.addWidget(card)

        wl.addWidget(cards_w)
        layout.addWidget(wrapper)

    # ── TRENDING NOW ──────────────────────────────────────────────────────
    def _build_trending(self, layout):
        hw = QWidget()
        hw.setStyleSheet("background: transparent;")
        hl = QVBoxLayout(hw)
        hl.setContentsMargins(40, 20, 40, 5)
        hdr = QLabel("Trending Now")
        hdr.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        hdr.setStyleSheet("color: white; background: transparent;")
        hl.addWidget(hdr)
        layout.addWidget(hw)

        scroll = QScrollArea()
        scroll.setFixedHeight(280)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        il = QHBoxLayout(inner)
        il.setContentsMargins(30, 0, 30, 0)
        il.setSpacing(10)

        movies = getattr(self.app, "movie_list", [])
        for m in (movies[:15] * 3):
            card = QWidget()
            card.setFixedWidth(160)
            card.setStyleSheet("background: transparent;")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            cl2 = QVBoxLayout(card)
            cl2.setContentsMargins(0, 0, 0, 0)
            cl2.setSpacing(6)

            img_lbl = QLabel()
            img_lbl.setFixedSize(150, 220)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet("background: #333; border-radius: 8px;")

            p_path = m.get("poster_local", "")
            if p_path and os.path.exists(p_path):
                key = (p_path, (150, 220))
                if key not in self.app._img_cache:
                    try:
                        self.app._img_cache[key] = pil_to_qpixmap(Image.open(p_path).convert("RGB"), (150, 220))
                    except: pass
                if key in self.app._img_cache:
                    img_lbl.setPixmap(self.app._img_cache[key])

            t = m.get("title", "Unknown")
            if len(t) > 18: t = t[:15] + "..."
            t_lbl = QLabel(t)
            t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t_lbl.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent;")
            t_lbl.setWordWrap(True)

            cl2.addWidget(img_lbl)
            cl2.addWidget(t_lbl)
            il.addWidget(card)

            for w in [card, img_lbl, t_lbl]:
                w.mousePressEvent = lambda e, d=m: self.app.show_page("moviedetail", d)

        il.addStretch()
        scroll.setWidget(inner)

        self._trend_scroll = scroll
        self._trend_pos = 0
        self._trend_timer = QTimer(self)
        self._trend_timer.timeout.connect(self._auto_scroll_trending)
        self._trend_timer.start(40)

        layout.addWidget(scroll)

    def _auto_scroll_trending(self):
        if not hasattr(self, '_trend_scroll'):
            return
        sb = self._trend_scroll.horizontalScrollBar()
        self._trend_pos += 1
        if self._trend_pos >= sb.maximum():
            self._trend_pos = 0
        sb.setValue(int(self._trend_pos))

    # ── TOP 10 ────────────────────────────────────────────────────────────
    def _build_top10(self, layout):
        container = QWidget()
        container.setStyleSheet("background: #F8F9FA; border-radius: 20px;")
        vl = QVBoxLayout(container)
        vl.setContentsMargins(40, 25, 40, 25)

        title = QLabel("Top 10 Movies")
        title.setFont(QFont("Helvetica", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A; background: transparent;")
        vl.addWidget(title)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 10, 0, 5)
        hl.setSpacing(0)
        for text, w in [("", 80), ("Film", 280), ("Year", 90), ("Mood", 150), ("Platform", 180), ("Synopsis", 0)]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #555; font-size: 14px; font-weight: bold; background: transparent;")
            if w: lbl.setFixedWidth(w)
            else: lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            hl.addWidget(lbl)
        vl.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background: #DDDDDD;")
        vl.addWidget(sep)

        for m in getattr(self.app, "movie_list", [])[:10]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 10, 0, 10)
            rl.setSpacing(0)

            def go(e, data=m): self.app.show_page("moviedetail", data)

            # Poster
            p_lbl = QLabel()
            p_lbl.setFixedSize(50, 75)
            p_lbl.setStyleSheet("background: #DDD; border-radius: 4px;")
            p_path = m.get("poster_local", "")
            if p_path and os.path.exists(p_path):
                key = (p_path, (50, 75))
                if key not in self.app._img_cache:
                    try: self.app._img_cache[key] = pil_to_qpixmap(Image.open(p_path).convert("RGB"), (50, 75))
                    except: pass
                if key in self.app._img_cache:
                    p_lbl.setPixmap(self.app._img_cache[key])

            pw = QWidget()
            pw.setFixedWidth(80)
            pw.setStyleSheet("background: transparent;")
            pwl = QHBoxLayout(pw)
            pwl.setContentsMargins(0, 0, 0, 0)
            pwl.addWidget(p_lbl)
            pwl.addStretch()
            rl.addWidget(pw)

            def mk(text, color, w=None, wrap=False):
                l = QLabel(text)
                l.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;")
                if w: l.setFixedWidth(w)
                if wrap: l.setWordWrap(True)
                return l

            t_lbl  = mk(m.get("title","N/A"), "#800000", 280, True)
            y_lbl  = mk(str(m.get("year","N/A")), "#1A1A1A", 90)
            g_lbl  = mk(m.get("genre","N/A").split(",")[0], "#2A52BE", 150)
            pl_lbl = mk(f"📺 {m.get('platform_string','N/A').split(',')[0].strip()}", "#2D5A27", 180)
            syn    = m.get("description", "No synopsis.")
            s_lbl  = mk((syn[:180]+"..") if len(syn)>180 else syn, "#444", wrap=True)
            s_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            for w in [t_lbl, y_lbl, g_lbl, pl_lbl, s_lbl]: rl.addWidget(w)
            for w in [row, p_lbl, pw, t_lbl, y_lbl, g_lbl, pl_lbl, s_lbl]: w.mousePressEvent = go

            vl.addWidget(row)
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background: #E0E0E0;")
            vl.addWidget(div)

        outer = QWidget()
        outer.setStyleSheet("background: transparent;")
        ol = QVBoxLayout(outer)
        ol.setContentsMargins(30, 20, 30, 0)
        ol.addWidget(container)
        layout.addWidget(outer)

    # ── TAGLINE ───────────────────────────────────────────────────────────
    def _build_tagline(self, layout):
        tl = QLabel('"Every story has a beginning."')
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.setFixedHeight(120)
        tl.setFont(QFont("Georgia", 32))
        tl.setStyleSheet("color: white; font-style: italic; background: #000000;")
        layout.addWidget(tl)

    # ── WATCHLIST BANNER ──────────────────────────────────────────────────
    def _build_watchlist_banner(self, layout):
        banner = QWidget()
        banner.setFixedHeight(160)
        banner.setStyleSheet("background: #FF8C00;")
        bl = QVBoxLayout(banner)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h = QLabel("Manage your watchlist now!")
        h.setFont(QFont("Georgia", 28))
        h.setStyleSheet("color: #111111; font-style: italic; font-weight: bold; background: transparent;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("GO TO WATCHLIST")
        btn.setFixedSize(200, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background: #111111; color: white; border-radius: 10px; font-size: 12px; font-weight: bold; border: none;")
        btn.clicked.connect(lambda: self.app.show_page("watchlist"))

        bl.addWidget(h)
        bl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

    # ── FOOTER ────────────────────────────────────────────────────────────
    def _build_footer(self, layout):
        footer = QWidget()
        footer.setFixedHeight(200)
        footer.setStyleSheet("background: #0A0A0A;")
        fl = QVBoxLayout(footer)
        fl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for text, font, color in [
            ("Cinephile Archive", QFont("Helvetica", 22, QFont.Weight.Bold), "white"),
            ("Created by Kelompok D5", QFont("Trebuchet MS", 14, QFont.Weight.Bold), ACCENT),
            ("Your Ultimate Cinematic Database © 2026", QFont("Trebuchet MS", 11), "gray"),
        ]:
            lbl = QLabel(text)
            lbl.setFont(font)
            lbl.setStyleSheet(f"color: {color}; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(lbl)

        layout.addWidget(footer)

    def closeEvent(self, event):
        self._carousel_timer.stop()
        if hasattr(self, '_trend_timer'):
            self._trend_timer.stop()
        super().closeEvent(event)
