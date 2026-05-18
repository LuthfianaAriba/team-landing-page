from __future__ import annotations

import os
import json
import io
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QMenu,
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


def pil_to_qpixmap(pil_img: Image.Image, size: tuple[int, int] | None = None) -> QPixmap:
    if size:
        try:
            pil_img = ImageOps.fit(pil_img, size, Image.LANCZOS)
        except Exception:
            pil_img = pil_img.resize(size, Image.LANCZOS)
    pil_img = pil_img.convert("RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))


# ══════════════════════════════════════════════════════════════════ NAVBAR
class NavBar(QWidget):
    def __init__(self, app: object, current_page: str = "dashboard") -> None:
        super().__init__()
        self.app = app
        self.setFixedHeight(60)
        self.setStyleSheet(f"background: {BG_NAV};")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(20, 0, 20, 0)
        root_layout.setSpacing(0)

        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json") as f:
                    self.username = json.load(f).get("username", "Guest")
        except Exception:
            pass

        # ── kiri: avatar + nama user ──────────────────────────────────────
        avatar = QLabel(self.username[0].upper())
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background: {ACCENT}; color: white; border-radius: 18px;"
            " font-weight: bold; font-size: 15px;"
        )

        user_btn = QPushButton(f"  {self.username} ▼")
        user_btn.setStyleSheet(
            "color: white; background: transparent; border: none;"
            " font-size: 13px; font-weight: bold;"
        )
        user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        user_btn.clicked.connect(self._show_profile_menu)

        left_w = QWidget()
        left_w.setFixedWidth(250)
        left_w.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_w)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_layout.addWidget(avatar)
        left_layout.addWidget(user_btn)
        left_layout.addStretch()

        # ── tengah: pill navigasi ─────────────────────────────────────────
        pill = QWidget()
        pill.setFixedHeight(34)
        pill.setStyleSheet("background: #2E2E2E; border-radius: 17px;")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(6, 3, 6, 3)
        pill_layout.setSpacing(2)

        # FIXED: ganti nama variabel 'w' → 'btn_w' supaya tidak bentrok dengan
        # variabel 'w' yang dipakai di loop lain (penyebab error Pylance)
        nav_items: list[tuple[str, str, int]] = [
            ("Home",           "dashboard",    70),
            ("Genre Analysis", "genreanalyze", 110),
            ("Movie Table",    "movietable",   92),
            ("Watchlist",      "watchlist",    80),
        ]
        for nav_text, nav_page, btn_w in nav_items:
            active = (nav_page == current_page)
            nav_btn = QPushButton(nav_text)
            nav_btn.setFixedSize(btn_w, 28)
            nav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            nav_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#E53935' if active else 'transparent'};
                    color: {'white' if active else '#AAAAAA'};
                    border-radius: 14px; font-size: 11px; font-weight: bold; border: none;
                }}
                QPushButton:hover {{
                    background: {'#C62828' if active else '#3A3A3A'};
                    color: white;
                }}
            """)
            nav_btn.clicked.connect(lambda _, p=nav_page: self.app.show_page(p))
            pill_layout.addWidget(nav_btn)

        # ── kanan: search bar ─────────────────────────────────────────────
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search movie...")
        self.search_entry.setFixedSize(200, 32)
        self.search_entry.setStyleSheet("""
            QLineEdit {
                background: #222; border: 1px solid #444; border-radius: 6px;
                color: white; font-size: 12px; padding: 0 8px;
            }
            QLineEdit:focus { border-color: #E53935; }
        """)
        self.search_entry.returnPressed.connect(self._do_search)

        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(40, 32)
        search_btn.setStyleSheet(
            "background: #E53935; border-radius: 6px; color: white;"
            " font-size: 14px; border: none;"
        )
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

        root_layout.addWidget(left_w)
        root_layout.addStretch()
        root_layout.addWidget(pill)
        root_layout.addStretch()
        root_layout.addWidget(right_w)

    def _do_search(self) -> None:
        self.app.handle_local_search(self.search_entry.text())

    def _show_profile_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1E1E1E; border: 1px solid #333; border-radius: 8px; color: white; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background: #2A2A2A; }
        """)
        menu.addAction(f"Hello, {self.username}!")
        menu.addSeparator()
        logout_action = menu.addAction("Logout")
        if logout_action:
            logout_action.triggered.connect(self._logout)
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def _logout(self) -> None:
        if os.path.exists("session.json"):
            os.remove("session.json")
        self.app.show_page("login")


# ══════════════════════════════════════════════════════════════ DASHBOARD
class DashboardPage(QWidget):
    def __init__(self, parent: QWidget, app: object) -> None:
        super().__init__(parent)
        self.app = app
        self.setStyleSheet(f"background: {BG_MAIN};")

        if not hasattr(self.app, "_img_cache"):
            self.app._img_cache = {}

        self._hero_pixmaps: list[QPixmap] = []
        self._current_hero = 0
        self._carousel_timer = QTimer(self)
        self._carousel_timer.timeout.connect(self._next_hero)

        self._build_ui()

    def _build_ui(self) -> None:
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
        self._build_insights(content_layout)
        self._build_trending(content_layout)
        self._build_top10(content_layout)
        self._build_tagline(content_layout)
        self._build_watchlist_banner(content_layout)
        self._build_footer(content_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ── HERO ──────────────────────────────────────────────────────────────
    def _build_hero(self, layout: QVBoxLayout) -> None:
        self.hero_label = QLabel()
        self.hero_label.setFixedHeight(400)
        self.hero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hero_label.setStyleSheet("background: #222222;")
        self.hero_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        base = os.path.dirname(os.path.abspath(__file__))
        for name in ["hero1.jpeg", "hero2.jpeg", "hero3.jpeg"]:
            path = os.path.join(base, name)
            if not os.path.exists(path):
                path = name
            if os.path.exists(path):
                try:
                    self._hero_pixmaps.append(
                        pil_to_qpixmap(Image.open(path).convert("RGB"))
                    )
                except Exception:
                    pass

        if self._hero_pixmaps:
            self._carousel_timer.start(5000)
            QTimer.singleShot(0, self._refresh_hero)

        layout.addWidget(self.hero_label)

    def _refresh_hero(self) -> None:
        if not self._hero_pixmaps:
            return
        w = self.hero_label.width() or self.width() or 1100
        h = 400
        px = self._hero_pixmaps[self._current_hero]
        scaled = px.scaled(
            w, 99999,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if scaled.height() > h:
            y_off = (scaled.height() - h) // 2
            scaled = scaled.copy(0, y_off, w, h)
        self.hero_label.setPixmap(scaled)

    def _next_hero(self) -> None:
        if not self._hero_pixmaps:
            return
        self._current_hero = (self._current_hero + 1) % len(self._hero_pixmaps)
        self._refresh_hero()

    def resizeEvent(self, event: object) -> None:  # type: ignore[override]
        super().resizeEvent(event)  # type: ignore[arg-type]
        self._refresh_hero()

    # ── INSIGHTS ──────────────────────────────────────────────────────────
    def _build_insights(self, layout: QVBoxLayout) -> None:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(40, 30, 40, 10)

        title = QLabel("Cinephile Insights")
        title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        wrapper_layout.addWidget(title)

        cards_w = QWidget()
        cards_w.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout(cards_w)
        cards_layout.setContentsMargins(0, 15, 0, 0)
        cards_layout.setSpacing(10)

        insight_items: list[tuple[str, str, str, str]] = [
            ("Total Movies",   "250 Titles",    "🎬", "#2d5a27"),
            ("Trending Genre", "Action/Sci-Fi", "🔥", "#2A368F"),
            ("Global Rating",  "4.9/5.0",       "⭐", "#8A4B1A"),
        ]
        for card_label, card_val, card_icon, card_color in insight_items:
            card = QWidget()
            card.setFixedHeight(100)
            card.setStyleSheet(f"background: {card_color}; border-radius: 15px;")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(20, 0, 20, 0)

            ico_lbl = QLabel(card_icon)
            ico_lbl.setFont(QFont("Arial", 32))
            ico_lbl.setStyleSheet("background: transparent;")

            info_w = QWidget()
            info_w.setStyleSheet("background: transparent;")
            info_layout = QVBoxLayout(info_w)
            info_layout.setContentsMargins(10, 0, 0, 0)
            info_layout.setSpacing(2)

            sub_lbl = QLabel(card_label)
            sub_lbl.setStyleSheet("color: #DDD; font-size: 13px; background: transparent;")
            val_lbl = QLabel(card_val)
            val_lbl.setFont(QFont("Arial Black", 18, QFont.Weight.Bold))
            val_lbl.setStyleSheet("color: white; background: transparent;")
            info_layout.addWidget(sub_lbl)
            info_layout.addWidget(val_lbl)

            card_layout.addWidget(ico_lbl)
            card_layout.addWidget(info_w)
            card_layout.addStretch()
            cards_layout.addWidget(card)

        wrapper_layout.addWidget(cards_w)
        layout.addWidget(wrapper)

    # ── TRENDING NOW ──────────────────────────────────────────────────────
    def _build_trending(self, layout: QVBoxLayout) -> None:
        header_w = QWidget()
        header_w.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_w)
        header_layout.setContentsMargins(40, 20, 40, 5)
        hdr = QLabel("Trending Now")
        hdr.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        hdr.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(hdr)
        layout.addWidget(header_w)

        scroll = QScrollArea()
        scroll.setFixedHeight(280)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(30, 0, 30, 0)
        inner_layout.setSpacing(10)

        movies: list[dict] = getattr(self.app, "movie_list", [])
        for movie in (movies[:15] * 3):
            card = QWidget()
            card.setFixedWidth(160)
            card.setStyleSheet("background: transparent;")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(6)

            img_lbl = QLabel()
            img_lbl.setFixedSize(150, 220)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet("background: #333; border-radius: 8px;")

            poster_path = movie.get("poster_local", "")
            if poster_path and os.path.exists(poster_path):
                cache_key = (poster_path, (150, 220))
                if cache_key not in self.app._img_cache:
                    try:
                        self.app._img_cache[cache_key] = pil_to_qpixmap(
                            Image.open(poster_path).convert("RGB"), (150, 220)
                        )
                    except Exception:
                        pass
                if cache_key in self.app._img_cache:
                    img_lbl.setPixmap(self.app._img_cache[cache_key])

            title_text = movie.get("title", "Unknown")
            if len(title_text) > 18:
                title_text = title_text[:15] + "..."
            title_lbl = QLabel(title_text)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_lbl.setStyleSheet(
                "color: white; font-size: 12px; font-weight: bold; background: transparent;"
            )
            title_lbl.setWordWrap(True)

            card_layout.addWidget(img_lbl)
            card_layout.addWidget(title_lbl)
            inner_layout.addWidget(card)

            # click handler
            for clickable in (card, img_lbl, title_lbl):
                clickable.mousePressEvent = (  # type: ignore[assignment]
                    lambda _e, d=movie: self.app.show_page("moviedetail", d)
                )

        inner_layout.addStretch()
        scroll.setWidget(inner)

        self._trend_scroll = scroll
        self._trend_pos = 0.0
        self._trend_timer = QTimer(self)
        self._trend_timer.timeout.connect(self._auto_scroll_trending)
        self._trend_timer.start(40)

        layout.addWidget(scroll)

    def _auto_scroll_trending(self) -> None:
        if not hasattr(self, "_trend_scroll"):
            return
        sb = self._trend_scroll.horizontalScrollBar()
        self._trend_pos += 1
        if self._trend_pos >= sb.maximum():
            self._trend_pos = 0.0
        sb.setValue(int(self._trend_pos))

    # ── TOP 10 ────────────────────────────────────────────────────────────
    def _build_top10(self, layout: QVBoxLayout) -> None:
        container = QWidget()
        container.setStyleSheet("background: #F8F9FA; border-radius: 20px;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 25, 40, 25)

        title = QLabel("Top 10 Movies")
        title.setFont(QFont("Helvetica", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A; background: transparent;")
        container_layout.addWidget(title)

        # header row
        header_w = QWidget()
        header_w.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_w)
        header_layout.setContentsMargins(0, 10, 0, 5)
        header_layout.setSpacing(0)

        # FIXED: variabel loop diubah dari 'w' → 'col_w' agar tidak bentrok
        header_cols: list[tuple[str, int]] = [
            ("", 80), ("Film", 280), ("Year", 90),
            ("Mood", 150), ("Platform", 180), ("Synopsis", 0),
        ]
        for col_text, col_w in header_cols:
            col_lbl = QLabel(col_text)
            col_lbl.setStyleSheet(
                "color: #555; font-size: 14px; font-weight: bold; background: transparent;"
            )
            if col_w:
                col_lbl.setFixedWidth(col_w)
            else:
                col_lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )
            header_layout.addWidget(col_lbl)
        container_layout.addWidget(header_w)

        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background: #DDDDDD;")
        container_layout.addWidget(sep)

        # FIXED: helper _make_lbl didefinisikan di luar loop agar tidak
        # ada variabel 'w' yang ambiguous di dalam nested function
        def _make_lbl(
            text: str,
            color: str,
            fixed_width: int = 0,
            wrap: bool = False,
        ) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;"
            )
            if fixed_width:
                lbl.setFixedWidth(fixed_width)
            if wrap:
                lbl.setWordWrap(True)
            return lbl

        movies: list[dict] = getattr(self.app, "movie_list", [])
        for movie in movies[:10]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 10, 0, 10)
            row_layout.setSpacing(0)

            def _go(_event: object, data: dict = movie) -> None:
                self.app.show_page("moviedetail", data)

            # poster thumbnail
            poster_lbl = QLabel()
            poster_lbl.setFixedSize(50, 75)
            poster_lbl.setStyleSheet("background: #DDD; border-radius: 4px;")
            poster_path = movie.get("poster_local", "")
            if poster_path and os.path.exists(poster_path):
                cache_key = (poster_path, (50, 75))
                if cache_key not in self.app._img_cache:
                    try:
                        self.app._img_cache[cache_key] = pil_to_qpixmap(
                            Image.open(poster_path).convert("RGB"), (50, 75)
                        )
                    except Exception:
                        pass
                if cache_key in self.app._img_cache:
                    poster_lbl.setPixmap(self.app._img_cache[cache_key])

            poster_wrap = QWidget()
            poster_wrap.setFixedWidth(80)
            poster_wrap.setStyleSheet("background: transparent;")
            poster_wrap_layout = QHBoxLayout(poster_wrap)
            poster_wrap_layout.setContentsMargins(0, 0, 0, 0)
            poster_wrap_layout.addWidget(poster_lbl)
            poster_wrap_layout.addStretch()
            row_layout.addWidget(poster_wrap)

            title_lbl  = _make_lbl(movie.get("title", "N/A"), "#800000", 280, True)
            year_lbl   = _make_lbl(str(movie.get("year", "N/A")), "#1A1A1A", 90)
            genre_lbl  = _make_lbl(movie.get("genre", "N/A").split(",")[0], "#2A52BE", 150)
            plat_text  = movie.get("platform_string", "N/A").split(",")[0].strip()
            plat_lbl   = _make_lbl(f"📺 {plat_text}", "#2D5A27", 180)
            syn_text   = movie.get("description", "No synopsis.")
            syn_lbl    = _make_lbl(
                (syn_text[:180] + "..") if len(syn_text) > 180 else syn_text,
                "#444", wrap=True,
            )
            syn_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            for cell in (title_lbl, year_lbl, genre_lbl, plat_lbl, syn_lbl):
                row_layout.addWidget(cell)

            # click handlers
            for clickable in (row, poster_lbl, poster_wrap, title_lbl,
                               year_lbl, genre_lbl, plat_lbl, syn_lbl):
                clickable.mousePressEvent = _go  # type: ignore[assignment]

            container_layout.addWidget(row)

            divider = QFrame()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background: #E0E0E0;")
            container_layout.addWidget(divider)

        outer = QWidget()
        outer.setStyleSheet("background: transparent;")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(30, 20, 30, 0)
        outer_layout.addWidget(container)
        layout.addWidget(outer)

    # ── TAGLINE ───────────────────────────────────────────────────────────
    def _build_tagline(self, layout: QVBoxLayout) -> None:
        tagline = QLabel('"Every story has a beginning."')
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setFixedHeight(120)
        tagline.setFont(QFont("Georgia", 32))
        tagline.setStyleSheet(
            "color: white; font-style: italic; background: #000000;"
        )
        layout.addWidget(tagline)

    # ── WATCHLIST BANNER ──────────────────────────────────────────────────
    def _build_watchlist_banner(self, layout: QVBoxLayout) -> None:
        banner = QWidget()
        banner.setFixedHeight(160)
        banner.setStyleSheet("background: #FF8C00;")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        headline = QLabel("Manage your watchlist now!")
        headline.setFont(QFont("Georgia", 28))
        headline.setStyleSheet(
            "color: #111111; font-style: italic; font-weight: bold; background: transparent;"
        )
        headline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        wl_btn = QPushButton("GO TO WATCHLIST")
        wl_btn.setFixedSize(200, 40)
        wl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wl_btn.setStyleSheet(
            "background: #111111; color: white; border-radius: 10px;"
            " font-size: 12px; font-weight: bold; border: none;"
        )
        wl_btn.clicked.connect(lambda: self.app.show_page("watchlist"))

        banner_layout.addWidget(headline)
        banner_layout.addWidget(wl_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

    # ── FOOTER ────────────────────────────────────────────────────────────
    def _build_footer(self, layout: QVBoxLayout) -> None:
        footer = QWidget()
        footer.setFixedHeight(200)
        footer.setStyleSheet("background: #0A0A0A;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FIXED: variabel loop 'fl' tidak lagi ambigu karena sudah
        # diberi nama eksplisit 'footer_layout' di atas
        footer_items: list[tuple[str, QFont, str]] = [
            ("Cinephile Archive",
             QFont("Helvetica", 22, QFont.Weight.Bold), "white"),
            ("Created by Kelompok D5",
             QFont("Trebuchet MS", 14, QFont.Weight.Bold), ACCENT),
            ("Your Ultimate Cinematic Database © 2026",
             QFont("Trebuchet MS", 11), "gray"),
        ]
        for ft_text, ft_font, ft_color in footer_items:
            ft_lbl = QLabel(ft_text)
            ft_lbl.setFont(ft_font)
            ft_lbl.setStyleSheet(f"color: {ft_color}; background: transparent;")
            ft_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            footer_layout.addWidget(ft_lbl)

        layout.addWidget(footer)

    # ── cleanup ───────────────────────────────────────────────────────────
    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        self._carousel_timer.stop()
        if hasattr(self, "_trend_timer"):
            self._trend_timer.stop()
        super().closeEvent(event)  # type: ignore[arg-type]
