import os
import io
from collections import Counter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QComboBox, QMenu
)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from PIL import Image, ImageOps

BG_MAIN   = "#1A1A1A"
BG_NAV    = "#111111"
ACCENT    = "#E53935"
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


class GenreAnalyzePage(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setStyleSheet(f"background: {BG_MAIN};")

        if not hasattr(self.app, '_img_cache'):
            self.app._img_cache = {}

        self.GENRE_DESCRIPTIONS = {
            "Action": "Focuses on high-energy sequences, physical feats, and thrilling chases or battles.",
            "Adventure": "Features characters traveling to new worlds or embarking on epic journeys to complete a mission.",
            "Animation": "Utilizes hand-drawn or computer-generated imagery to bring imaginative stories and characters to life.",
            "Biography": "Tells the real-life story of a person, focusing on their experiences, achievements, and legacy.",
            "Comedy": "Intended to provoke laughter through humor, irony, or witty dialogue and situations.",
            "Crime": "Features criminal activities, investigations, law enforcement, and the pursuit of justice.",
            "Drama": "Explores the human condition, emotional conflict, and realistic character development.",
            "Family": "Designed to appeal to all ages, focusing on themes like friendship, family values, and growth.",
            "Fantasy": "Involves magical elements, mythical creatures, and extraordinary worlds beyond reality.",
            "History": "Recreates historical events, periods, or figures with attention to factual details and atmosphere.",
            "Horror": "Designed to evoke fear, suspense, and shock through supernatural or psychological elements.",
            "Music": "Focuses on the lives of musicians, the creative process, or utilizes music as a central narrative theme.",
            "Musical": "Features characters who burst into song and dance to express emotions or advance the plot.",
            "Mystery": "Centers on solving a puzzle, crime, or unexplained event through clues and investigation.",
            "Romance": "Focuses on love stories, emotional relationships, and the journey of finding a partner.",
            "Sci-Fi": "Explores futuristic concepts, advanced science, technology, space exploration, and extraterrestrial life.",
            "Thriller": "Emphasizes suspense, excitement, and high-stakes tension to keep viewers on the edge of their seats.",
            "War": "Focuses on armed conflict, the struggles of soldiers, and the impact of battle on society.",
            "Western": "Set in the American Old West, featuring cowboys, outlaws, and the struggle for law and order.",
        }

        self.analyzed_data = self._process_genre_logic()
        self.all_years, self.yearly_top = self._process_yearly_data()
        self._carousel_offset = 0
        self._carousel_movies = []

        self._build_ui()

    # ── HELPERS ───────────────────────────────────────────────────────────
    def _process_genre_logic(self):
        all_genres = []
        for movie in getattr(self.app, "movie_list", []):
            raw = movie.get("genre", "Unknown")
            if raw and raw not in ["Unknown", "N/A"]:
                all_genres.extend([g.strip() for g in raw.split(",")])
        counts = Counter(all_genres)
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)

    def _process_yearly_data(self):
        year_data = {}
        for movie in getattr(self.app, "movie_list", []):
            year_str = "".join(filter(str.isdigit, str(movie.get("year", ""))))[:4]
            if not year_str or len(year_str) != 4:
                continue
            raw = movie.get("genre", "Unknown")
            if raw and raw not in ["Unknown", "N/A"]:
                genres = [g.strip() for g in raw.split(",")]
                year_data.setdefault(year_str, []).extend(genres)
        yearly_top = {}
        for y, gl in year_data.items():
            if gl:
                top_genre, count = Counter(gl).most_common(1)[0]
                yearly_top[y] = (top_genre, count)
        return sorted(yearly_top.keys()), yearly_top

    def _get_genre_desc(self, name):
        return self.GENRE_DESCRIPTIONS.get(name, f"Discover our top recommendations for the {name} genre.")

    def _load_pixmap(self, path, size):
        key = (path, size)
        if key not in self.app._img_cache:
            try:
                self.app._img_cache[key] = pil_to_qpixmap(Image.open(path).convert("RGB"), size)
            except:
                return None
        return self.app._img_cache[key]

    # ── BUILD UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_nav())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setStyleSheet(f"background: {BG_MAIN};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        bl.addWidget(self._build_hero())
        bl.addWidget(self._build_two_col())
        bl.addWidget(self._build_top_recommendations())
        bl.addWidget(self._build_orange_banner())
        bl.addWidget(self._build_footer())

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

    # ── NAVBAR ────────────────────────────────────────────────────────────
    def _build_nav(self):
        nav = QWidget()
        nav.setFixedHeight(60)
        nav.setStyleSheet(f"background: {BG_NAV};")

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # Dummy kiri (counterweight search)
        dummy = QWidget()
        dummy.setFixedWidth(200)
        dummy.setStyleSheet("background: transparent;")
        layout.addWidget(dummy)

        # Pill center
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
            active = (page == "genreanalyze")
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

        layout.addStretch()
        layout.addWidget(pill)
        layout.addStretch()

        # Search
        search_w = QWidget()
        search_w.setFixedWidth(200)
        search_w.setStyleSheet("background: transparent;")
        sl = QHBoxLayout(search_w)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(5)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search...")
        self.search_entry.setFixedSize(150, 32)
        self.search_entry.setStyleSheet("""
            QLineEdit { background: #222; border: 1px solid #444; border-radius: 6px;
                        color: white; font-size: 12px; padding: 0 8px; }
        """)
        self.search_entry.returnPressed.connect(lambda: self.app.handle_local_search(self.search_entry.text()))

        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(40, 32)
        search_btn.setStyleSheet(f"background: {ACCENT}; border-radius: 6px; color: white; font-size: 14px; border: none;")
        search_btn.clicked.connect(lambda: self.app.handle_local_search(self.search_entry.text()))

        sl.addWidget(self.search_entry)
        sl.addWidget(search_btn)
        layout.addWidget(search_w)

        return nav

    # ── HERO ──────────────────────────────────────────────────────────────
    def _build_hero(self):
        widget = QWidget()
        widget.setStyleSheet(f"background: {BG_MAIN};")
        wl = QVBoxLayout(widget)
        wl.setContentsMargins(0, 60, 0, 10)
        wl.setSpacing(0)

        title = QLabel("Genre Analyze")
        title.setFont(QFont("Helvetica", 70, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(title)

        # Carousel
        carousel_area = QScrollArea()
        carousel_area.setFixedHeight(140)
        carousel_area.setWidgetResizable(True)
        carousel_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        carousel_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        carousel_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._carousel_inner = QWidget()
        self._carousel_inner.setStyleSheet("background: transparent;")
        self._carousel_layout = QHBoxLayout(self._carousel_inner)
        self._carousel_layout.setContentsMargins(20, 5, 20, 5)
        self._carousel_layout.setSpacing(12)

        movie_list = getattr(self.app, "movie_list", [])
        self._carousel_movies = [m for m in movie_list
                                  if m.get("poster_local") and os.path.exists(m.get("poster_local", ""))]
        sample = self._carousel_movies[:12]

        for movie in sample * 2:
            px = self._load_pixmap(movie.get("poster_local"), (85, 120))
            if px:
                lbl = QLabel()
                lbl.setPixmap(px)
                lbl.setFixedSize(85, 120)
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.mousePressEvent = lambda e, d=movie: self.app.show_page("moviedetail", d)
                self._carousel_layout.addWidget(lbl)

        self._carousel_layout.addStretch()
        carousel_area.setWidget(self._carousel_inner)
        wl.addSpacing(20)
        wl.addWidget(carousel_area)

        # Auto scroll carousel
        self._carousel_scroll = carousel_area
        self._carousel_pos = 0
        self._carousel_timer = QTimer(self)
        self._carousel_timer.timeout.connect(self._scroll_carousel)
        self._carousel_timer.start(30)

        return widget

    def _scroll_carousel(self):
        sb = self._carousel_scroll.horizontalScrollBar()
        self._carousel_pos += 1
        if self._carousel_pos >= sb.maximum():
            self._carousel_pos = 0
        sb.setValue(int(self._carousel_pos))

    # ── TWO COLUMN ────────────────────────────────────────────────────────
    def _build_two_col(self):
        widget = QWidget()
        widget.setStyleSheet(f"background: {BG_MAIN};")
        wl = QHBoxLayout(widget)
        wl.setContentsMargins(100, 40, 100, 40)
        wl.setSpacing(80)

        wl.addWidget(self._build_genre_distribution(), stretch=1)
        wl.addWidget(self._build_right_col(), stretch=1)

        return widget

    def _build_genre_distribution(self):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        title = QLabel("Genre Distribution")
        title.setFont(QFont("Georgia", 36))
        title.setStyleSheet("color: white; font-style: italic; background: transparent;")
        vl.addWidget(title)
        vl.addSpacing(10)

        top_10 = self.analyzed_data[:10]
        if not top_10:
            vl.addWidget(QLabel("No data"))
            return widget

        max_val = top_10[0][1]
        for genre, count in top_10:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(10)

            lbl = QLabel(f"{genre} ({count})")
            lbl.setFixedWidth(130)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color: white; font-size: 13px; font-weight: bold; background: transparent;")
            rl.addWidget(lbl)

            bar_w = max(5, int((count / max_val) * 300))
            bar = QWidget()
            bar.setFixedSize(bar_w, 22)
            bar.setStyleSheet(f"background: {ACCENT}; border-radius: 2px;")
            rl.addWidget(bar)
            rl.addStretch()

            row.mousePressEvent = lambda e, g=genre: self.app.handle_local_search(g)
            vl.addWidget(row)

        vl.addStretch()
        return widget

    def _build_right_col(self):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # Overview
        ov_title = QLabel("OVERVIEW")
        ov_title.setFont(QFont("Trebuchet MS", 12, QFont.Weight.Bold))
        ov_title.setStyleSheet(f"color: {TEXT_GRAY}; background: transparent;")
        vl.addWidget(ov_title)
        vl.addSpacing(5)

        ov_text = QLabel("Analyze your movie collection's DNA.\nThis section provides insights into your\nmost watched genres and trends.")
        ov_text.setFont(QFont("Trebuchet MS", 14))
        ov_text.setStyleSheet("color: white; background: transparent;")
        ov_text.setWordWrap(True)
        vl.addWidget(ov_text)

        vl.addSpacing(50)

        # Yearly Trends
        trend_title = QLabel("Yearly Trends")
        trend_title.setFont(QFont("Georgia", 32))
        trend_title.setStyleSheet("color: white; font-style: italic; background: transparent;")
        vl.addWidget(trend_title)
        vl.addSpacing(10)

        if not self.all_years:
            vl.addWidget(QLabel("No yearly data found."))
            vl.addStretch()
            return widget

        # Filter row
        filter_w = QWidget()
        filter_w.setStyleSheet("background: transparent;")
        fl = QHBoxLayout(filter_w)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(8)

        combo_style = """
            QComboBox { background: #2B2B2B; border: 1px solid #444; border-radius: 6px;
                        color: white; font-size: 13px; padding: 0 8px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #2B2B2B; color: white; }
        """
        sorted_years = sorted(self.all_years)

        self.start_combo = QComboBox()
        self.start_combo.addItems(sorted_years)
        self.start_combo.setFixedSize(100, 34)
        self.start_combo.setStyleSheet(combo_style)

        self.end_combo = QComboBox()
        self.end_combo.addItems(sorted_years)
        self.end_combo.setCurrentIndex(len(sorted_years) - 1)
        self.end_combo.setFixedSize(100, 34)
        self.end_combo.setStyleSheet(combo_style)

        dash = QLabel(" - ")
        dash.setStyleSheet("color: white; background: transparent; font-size: 16px;")

        filter_btn = QPushButton("Filter")
        filter_btn.setFixedSize(70, 34)
        filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 1px solid {ACCENT}; color: white;
                          border-radius: 6px; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ background: #441111; }}
        """)
        filter_btn.clicked.connect(self._update_trends)

        fl.addWidget(self.start_combo)
        fl.addWidget(dash)
        fl.addWidget(self.end_combo)
        fl.addWidget(filter_btn)
        fl.addStretch()
        vl.addWidget(filter_w)
        vl.addSpacing(15)

        self.trend_display = QWidget()
        self.trend_display.setStyleSheet("background: transparent;")
        self.trend_layout = QVBoxLayout(self.trend_display)
        self.trend_layout.setContentsMargins(0, 0, 0, 0)
        self.trend_layout.setSpacing(6)
        vl.addWidget(self.trend_display)

        self._update_trends()
        vl.addStretch()
        return widget

    def _update_trends(self):
        # Clear
        while self.trend_layout.count():
            item = self.trend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            s = int(self.start_combo.currentText())
            e = int(self.end_combo.currentText())
            if s > e: s, e = e, s
        except:
            return

        valid = sorted([y for y in self.all_years if s <= int(y) <= e], reverse=True)
        if not valid:
            return

        max_c = max(self.yearly_top[y][1] for y in valid)

        for year in valid:
            genre, count = self.yearly_top[year]
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)

            y_lbl = QLabel(str(year))
            y_lbl.setFixedWidth(50)
            y_lbl.setStyleSheet("color: white; font-size: 13px; font-weight: bold; background: transparent;")
            rl.addWidget(y_lbl)

            bar_w = max(5, int((count / max_c) * 160))
            bar = QWidget()
            bar.setFixedSize(bar_w, 16)
            bar.setStyleSheet(f"background: {ACCENT};")
            rl.addWidget(bar)

            g_lbl = QLabel(f"{genre} ({count})")
            g_lbl.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 12px; background: transparent;")
            rl.addWidget(g_lbl)
            rl.addStretch()

            self.trend_layout.addWidget(row)

    # ── TOP RECOMMENDATIONS ───────────────────────────────────────────────
    def _build_top_recommendations(self):
        widget = QWidget()
        widget.setStyleSheet(f"background: {BG_MAIN};")
        wl = QVBoxLayout(widget)
        wl.setContentsMargins(100, 0, 100, 40)
        wl.setSpacing(0)

        top_3 = self.analyzed_data[:3]
        movie_list = getattr(self.app, "movie_list", [])

        for i, (name, count) in enumerate(top_3):
            cat = QWidget()
            cat.setStyleSheet("background: transparent;")
            cl = QVBoxLayout(cat)
            cl.setContentsMargins(0, 40, 0, 0)
            cl.setSpacing(0)

            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("Helvetica", 36, QFont.Weight.Bold))
            name_lbl.setStyleSheet("color: white; background: transparent;")
            cl.addWidget(name_lbl)

            desc_lbl = QLabel(self._get_genre_desc(name))
            desc_lbl.setFont(QFont("Trebuchet MS", 14))
            desc_lbl.setStyleSheet(f"color: {TEXT_GRAY}; background: transparent;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setMaximumWidth(650)
            cl.addSpacing(10)
            cl.addWidget(desc_lbl)

            cl.addSpacing(20)

            poster_row = QWidget()
            poster_row.setStyleSheet("background: transparent;")
            pr = QHBoxLayout(poster_row)
            pr.setContentsMargins(0, 0, 0, 0)
            pr.setSpacing(18)
            pr.setAlignment(Qt.AlignmentFlag.AlignLeft)

            matches = [m for m in movie_list
                       if name in [g.strip() for g in m.get("genre", "").split(",")]]
            for m_data in matches[:5]:
                path = m_data.get("poster_local", "")
                if path and os.path.exists(path):
                    px = self._load_pixmap(path, (120, 175))
                    if px:
                        lbl = QLabel()
                        lbl.setPixmap(px)
                        lbl.setFixedSize(120, 175)
                        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                        lbl.mousePressEvent = lambda e, d=m_data: self.app.show_page("moviedetail", d)
                        pr.addWidget(lbl)

            pr.addStretch()
            cl.addWidget(poster_row)

            if i < len(top_3) - 1:
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet("background: #333;")
                cl.addSpacing(20)
                cl.addWidget(sep)

            wl.addWidget(cat)

        return widget

    # ── ORANGE BANNER ─────────────────────────────────────────────────────
    def _build_orange_banner(self):
        banner = QWidget()
        banner.setFixedHeight(160)
        banner.setStyleSheet("background: #FF8C00;")
        bl = QVBoxLayout(banner)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.setSpacing(0)

        h = QLabel("Ready for a movie marathon?")
        h.setFont(QFont("Georgia", 30))
        h.setStyleSheet("color: #111111; font-style: italic; background: transparent;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(h)
        bl.addSpacing(15)

        btn = QPushButton("Open Watchlist")
        btn.setFixedSize(160, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background: #111111; color: white; border-radius: 4px; font-size: 13px; font-weight: bold; border: none;")
        btn.clicked.connect(lambda: self.app.show_page("watchlist"))
        bl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return banner

    # ── FOOTER ────────────────────────────────────────────────────────────
    def _build_footer(self):
        footer = QWidget()
        footer.setFixedHeight(180)
        footer.setStyleSheet("background: #0A0A0A;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(40, 0, 40, 0)

        left = QLabel("Cinephile")
        left.setFont(QFont("Helvetica", 55, QFont.Weight.Bold))
        left.setStyleSheet("color: white; background: transparent;")

        right = QLabel("©2026 Cinephile Archive\nCurating cinematic excellence for your personal collection.")
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 12px; background: transparent;")

        fl.addWidget(left)
        fl.addStretch()
        fl.addWidget(right)

        return footer

    def closeEvent(self, event):
        if hasattr(self, '_carousel_timer'):
            self._carousel_timer.stop()
        super().closeEvent(event)
