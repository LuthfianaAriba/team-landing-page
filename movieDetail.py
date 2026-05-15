import os
import json
import math
import random
import io
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QComboBox, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
from PIL import Image, ImageFilter, ImageEnhance
from dashboardCinephile import NavBar, pil_to_qpixmap


class MovieDetailPage(QWidget):
    def __init__(self, parent, app, movie_data=None):
        super().__init__(parent)
        self.app = app
        self.movie = movie_data if movie_data else {}
        self.star_buttons = []
        self.selected_stars = 0
        self._more_movies = None

        if not hasattr(self.app, '_img_cache'):
            self.app._img_cache = {}

        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json", "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", data.get("active_user", "Guest"))
        except: pass

        self.setStyleSheet("background: #141414;")
        self._build_ui()

    def _load_image(self, path, size):
        key = (path, size)
        if key not in self.app._img_cache:
            img = Image.open(path).convert("RGB")
            self.app._img_cache[key] = pil_to_qpixmap(img, size)
        return self.app._img_cache[key]

    def _generate_dynamic_chart(self, rating_str, votes_str="0"):
        try:
            rating = float(rating_str)
        except:
            rating = 5.0
        try:
            total_votes = int(str(votes_str).replace(",", "").replace(".", "").replace(" ", ""))
        except:
            total_votes = 0

        distribution = {}
        for score in range(1, 11):
            distance = abs(score - rating)
            weight = math.exp(-(distance ** 2) / 2.0)
            noise = random.uniform(0.8, 1.2)
            distribution[score] = weight * noise
        total_weight = sum(distribution.values())
        for score in distribution:
            distribution[score] = distribution[score] / total_weight
        return distribution, total_votes

    def _load_existing_review(self):
        wl_file = f"watchlist_{self.username}.json"
        if os.path.exists(wl_file):
            try:
                with open(wl_file, "r", encoding="utf-8") as f:
                    for m in json.load(f):
                        if m.get("title") == self.movie.get("title"):
                            return m.get("user_rating", 0), m.get("user_review", "")
            except: pass
        return 0, ""

    def _on_status_change(self, value):
        if value == "Plan to Watch":
            self.selected_stars = 0
            for btn in self.star_buttons:
                btn.setText("☆")
                btn.setStyleSheet(btn.styleSheet().replace("#FF8C00", "#2A2A2A"))
                btn.setEnabled(False)
        else:
            for i, btn in enumerate(self.star_buttons):
                btn.setEnabled(True)
                if i < self.selected_stars:
                    btn.setText("★")
                    btn.setStyleSheet(self._star_style("#FF8C00"))
                else:
                    btn.setText("☆")
                    btn.setStyleSheet(self._star_style("#555555"))

    def _star_style(self, color):
        return f"color: {color}; background: transparent; border: none; font-size: 17px;"

    def _set_stars(self, count):
        if self.status_combo.currentText() == "Plan to Watch":
            return
        self.selected_stars = count
        for i, btn in enumerate(self.star_buttons):
            if i < count:
                btn.setText("★")
                btn.setStyleSheet(self._star_style("#FF8C00"))
            else:
                btn.setText("☆")
                btn.setStyleSheet(self._star_style("#555555"))

    def _go_to_genre(self, genre):
        self.app.search_query_pending = genre
        self.app.show_page("movietable")

    def _add_to_watchlist(self):
        status = self.status_combo.currentText()
        wl_file = f"watchlist_{self.username}.json"
        watchlist = []
        if os.path.exists(wl_file):
            try:
                with open(wl_file, "r", encoding="utf-8") as f:
                    watchlist = json.load(f)
            except: pass

        user_rating = self.selected_stars
        user_review = self.review_entry.toPlainText().strip()

        movie_exists = False
        for m in watchlist:
            if m.get("title") == self.movie.get("title"):
                m["status"] = status
                if user_rating > 0: m["user_rating"] = user_rating
                if user_review: m["user_review"] = user_review
                movie_exists = True
                break

        if not movie_exists:
            new_entry = self.movie.copy()
            new_entry["status"] = status
            if user_rating > 0: new_entry["user_rating"] = user_rating
            if user_review: new_entry["user_review"] = user_review
            watchlist.append(new_entry)

        with open(wl_file, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, indent=4)

        self.add_btn.setText(f"✓ Saved as {status}")
        self.add_btn.setStyleSheet("background: #28a745; color: black; font-size: 15px; font-weight: bold; border-radius: 8px; border: none;")

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(NavBar(self.app, ""))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #141414; }")

        content = QWidget()
        content.setStyleSheet("background: #141414;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # ── Data ──
        title         = self.movie.get("title", "Unknown Title")
        year          = self.movie.get("year", "N/A")
        rating_val    = self.movie.get("rating", "N/A")
        votes_val     = self.movie.get("votes", "0")
        poster_path   = self.movie.get("poster_local", "")
        raw_genre     = self.movie.get("genre", "General")
        genres        = [g.strip() for g in raw_genre.split(",")] if isinstance(raw_genre, str) else ["Action"]
        synopsis_full = self.movie.get("synopsis", self.movie.get("description", "No synopsis available."))

        # ── 1. HERO ──
        hero = QWidget()
        hero.setFixedHeight(340)
        hero.setStyleSheet("background: #1c1c1c;")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(50, 20, 50, 20)
        hero_layout.setSpacing(30)

        # Blurred BG
        if poster_path and os.path.exists(poster_path):
            try:
                bg_img = Image.open(poster_path).convert("RGB")
                ratio = max(800 / bg_img.width, 227 / bg_img.height)
                bg_img = bg_img.resize((int(bg_img.width*ratio), int(bg_img.height*ratio)), Image.LANCZOS)
                l = (bg_img.width - 800) // 2
                t = (bg_img.height - 227) // 2
                bg_img = bg_img.crop((l, t, l+800, t+227))
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=12))
                bg_img = ImageEnhance.Brightness(bg_img).enhance(0.25)
                hero.setAutoFillBackground(True)
                px = pil_to_qpixmap(bg_img, (1200, 340))
                bg_lbl = QLabel(hero)
                bg_lbl.setPixmap(px)
                bg_lbl.setGeometry(0, 0, 1200, 340)
                bg_lbl.lower()
            except: pass

        # Poster thumb
        if poster_path and os.path.exists(poster_path):
            try:
                px = self._load_image(poster_path, (160, 240))
                poster_lbl = QLabel()
                poster_lbl.setPixmap(px)
                poster_lbl.setFixedSize(160, 240)
                hero_layout.addWidget(poster_lbl)
            except: pass

        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_vl = QVBoxLayout(info_widget)
        info_vl.setContentsMargins(0, 0, 0, 0)
        info_vl.setSpacing(8)

        title_text = f"{title} ({year})" if year != "N/A" else title
        font_size = 28 if len(title_text) > 40 else 34
        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont("Palatino Linotype", font_size))
        title_lbl.setStyleSheet("color: white; font-style: italic; background: transparent;")
        title_lbl.setWordWrap(True)
        info_vl.addWidget(title_lbl)

        genre_row = QHBoxLayout()
        for g in genres[:3]:
            gbtn = QPushButton(g)
            gbtn.setFixedSize(80, 28)
            gbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            gbtn.setStyleSheet("background: #990000; color: white; border-radius: 14px; font-size: 12px; border: none;")
            gbtn.clicked.connect(lambda _, gn=g: self._go_to_genre(gn))
            genre_row.addWidget(gbtn)
        genre_row.addStretch()
        info_vl.addLayout(genre_row)

        rating_lbl = QLabel(f"★ {rating_val}/10")
        rating_lbl.setFont(QFont("Helvetica", 22, QFont.Weight.Bold))
        rating_lbl.setStyleSheet("color: #FF3333; background: transparent;")
        info_vl.addWidget(rating_lbl)
        info_vl.addStretch()

        hero_layout.addWidget(info_widget)
        hero_layout.addStretch()
        cl.addWidget(hero)

        # ── Konten Bawah ──
        content_inner = QWidget()
        content_inner.setStyleSheet("background: transparent;")
        inner_vl = QVBoxLayout(content_inner)
        inner_vl.setContentsMargins(50, 0, 50, 0)
        inner_vl.setSpacing(0)

        # 2. Synopsis
        syn_row = QHBoxLayout()
        syn_row.setContentsMargins(0, 20, 0, 20)
        syn_title = QLabel("Synopsis")
        syn_title.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        syn_title.setStyleSheet("color: #FF8C00; background: transparent;")
        syn_title.setFixedWidth(120)
        syn_title.setAlignment(Qt.AlignmentFlag.AlignTop)
        syn_lbl = QLabel(synopsis_full)
        syn_lbl.setStyleSheet("color: #DDDDDD; font-size: 15px; background: transparent;")
        syn_lbl.setWordWrap(True)
        syn_row.addWidget(syn_title)
        syn_row.addWidget(syn_lbl)
        inner_vl.addLayout(syn_row)

        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background: #333;")
        inner_vl.addWidget(sep1)

        # 3. Where to Watch
        wtw_row = QHBoxLayout()
        wtw_row.setContentsMargins(0, 10, 0, 10)
        wtw_lbl = QLabel("Where To Watch:")
        wtw_lbl.setFont(QFont("Helvetica", 14, QFont.Weight.Bold))
        wtw_lbl.setStyleSheet("color: white; background: transparent;")
        wtw_row.addWidget(wtw_lbl)
        platform_str = self.movie.get("platform_string", "")
        platforms = [p.strip() for p in platform_str.split(",")] if platform_str else []
        if platforms:
            for p in platforms[:4]:
                pb = QPushButton(p)
                pb.setFixedHeight(30)
                pb.setStyleSheet("background: #222; color: white; border-radius: 15px; padding: 0 12px; font-size: 12px; border: none;")
                wtw_row.addWidget(pb)
        else:
            wtw_row.addWidget(QLabel("Not Available Online"))
        wtw_row.addStretch()
        inner_vl.addLayout(wtw_row)

        # 4. Chart + Watchlist
        split_row = QHBoxLayout()
        split_row.setContentsMargins(0, 40, 0, 20)
        split_row.setSpacing(80)

        # Chart
        chart_widget = QWidget()
        chart_widget.setStyleSheet("background: transparent;")
        chart_vl = QVBoxLayout(chart_widget)
        chart_vl.setContentsMargins(0, 0, 0, 0)
        chart_vl.setSpacing(5)

        chart_title = QLabel("Ratings Distribution")
        chart_title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        chart_title.setStyleSheet("color: white; background: transparent;")
        chart_vl.addWidget(chart_title)

        ratings_data, total_votes = self._generate_dynamic_chart(rating_val, votes_val)
        for score in sorted(ratings_data.keys(), reverse=True):
            value = ratings_data[score]
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_hl = QHBoxLayout(row_w)
            row_hl.setContentsMargins(0, 0, 0, 0)
            row_hl.setSpacing(10)

            score_lbl = QLabel(str(score))
            score_lbl.setFixedWidth(24)
            score_lbl.setStyleSheet("color: white; font-size: 14px; background: transparent;")
            row_hl.addWidget(score_lbl)

            bar = QWidget()
            fill_width = max(5, int(value * 450))
            bar.setFixedSize(fill_width, 24)
            bar.setStyleSheet("background: #C00000; border-radius: 2px;")
            row_hl.addWidget(bar)
            row_hl.addStretch()
            chart_vl.addWidget(row_w)

        # Votes label
        votes_display = f"{total_votes:,}" if total_votes > 0 else "N/A"
        votes_lbl = QLabel(f"👥  {votes_display} ratings")
        votes_lbl.setStyleSheet("color: #AAAAAA; font-size: 16px; background: transparent;")
        chart_vl.addSpacing(14)
        chart_vl.addWidget(votes_lbl)
        chart_vl.addStretch()

        split_row.addWidget(chart_widget)

        # Watchlist panel
        wl_panel = QWidget()
        wl_panel.setStyleSheet("background: #1E1E1E; border-radius: 15px;")
        wl_vl = QVBoxLayout(wl_panel)
        wl_vl.setContentsMargins(30, 30, 30, 30)
        wl_vl.setSpacing(10)

        wl_title = QLabel("Manage Watchlist")
        wl_title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        wl_title.setStyleSheet("color: white; background: transparent;")
        wl_vl.addWidget(wl_title)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Plan to Watch", "Watched", "Watching"])
        self.status_combo.setFixedSize(250, 40)
        self.status_combo.setStyleSheet("""
            QComboBox { background: #333; color: white; border-radius: 6px;
                        font-size: 14px; padding: 0 10px; border: none; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #333; color: white; }
        """)
        self.status_combo.currentTextChanged.connect(self._on_status_change)
        wl_vl.addWidget(self.status_combo)

        sep_wl = QFrame()
        sep_wl.setFixedHeight(1)
        sep_wl.setStyleSheet("background: #333;")
        wl_vl.addWidget(sep_wl)

        review_title = QLabel("My Review")
        review_title.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        review_title.setStyleSheet("color: #FF8C00; background: transparent;")
        wl_vl.addWidget(review_title)

        star_row = QHBoxLayout()
        rating_lbl2 = QLabel("Rating:")
        rating_lbl2.setStyleSheet("color: #AAAAAA; font-size: 13px; background: transparent;")
        star_row.addWidget(rating_lbl2)

        self.star_buttons = []
        for i in range(1, 11):
            btn = QPushButton("☆")
            btn.setFixedSize(26, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._star_style("#555555"))
            btn.clicked.connect(lambda _, n=i: self._set_stars(n))
            self.star_buttons.append(btn)
            star_row.addWidget(btn)
        star_row.addStretch()
        wl_vl.addLayout(star_row)

        existing_rating, existing_review = self._load_existing_review()
        if existing_rating > 0:
            self._set_stars(existing_rating)
        self._on_status_change(self.status_combo.currentText())

        notes_lbl = QLabel("Notes / Review:")
        notes_lbl.setStyleSheet("color: #AAAAAA; font-size: 13px; background: transparent;")
        wl_vl.addWidget(notes_lbl)

        self.review_entry = QTextEdit()
        self.review_entry.setFixedSize(250, 90)
        self.review_entry.setStyleSheet("""
            QTextEdit { background: #2A2A2A; color: white; font-size: 13px;
                        border-radius: 8px; border: none; padding: 6px; }
        """)
        if existing_review:
            self.review_entry.setPlainText(existing_review)
        wl_vl.addWidget(self.review_entry)

        self.add_btn = QPushButton("+ Update Watchlist")
        self.add_btn.setFixedSize(250, 45)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("background: #FF8C00; color: black; font-size: 15px; font-weight: bold; border-radius: 8px; border: none;")
        self.add_btn.clicked.connect(self._add_to_watchlist)
        wl_vl.addWidget(self.add_btn)

        split_row.addWidget(wl_panel)
        inner_vl.addLayout(split_row)

        # 5. More Stories
        more_row = QHBoxLayout()
        more_row.setContentsMargins(0, 70, 0, 40)
        more_title = QLabel("More Stories")
        more_title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        more_title.setStyleSheet("color: white; background: transparent;")
        more_title.setFixedWidth(150)
        more_title.setAlignment(Qt.AlignmentFlag.AlignTop)
        more_row.addWidget(more_title)

        all_movies = getattr(self.app, "movie_list", [])
        other_movies = [m for m in all_movies if m.get("title") != title]
        if other_movies:
            if self._more_movies is None:
                self._more_movies = random.sample(other_movies, min(len(other_movies), 4))
            for m_data in self._more_movies:
                m_path = m_data.get("poster_local", "")
                if m_path and os.path.exists(m_path):
                    try:
                        px = self._load_image(m_path, (140, 200))
                        lbl = QLabel()
                        lbl.setPixmap(px)
                        lbl.setFixedSize(140, 200)
                        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                        lbl.mousePressEvent = lambda e, d=m_data: self.app.show_page("moviedetail", d)
                        more_row.addWidget(lbl)
                    except: pass
        more_row.addStretch()
        inner_vl.addLayout(more_row)

        cl.addWidget(content_inner)

        # 6. Banner Footer
        banner = QWidget()
        banner.setFixedHeight(120)
        banner.setStyleSheet("background: #FF8C00;")
        bl = QVBoxLayout(banner)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bh = QLabel("Ready to track more movies?")
        bh.setFont(QFont("Georgia", 22))
        bh.setStyleSheet("color: black; font-style: italic; background: transparent;")
        bh.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(bh)

        bb = QPushButton("Go to Watchlist")
        bb.setFixedSize(160, 36)
        bb.setCursor(Qt.CursorShape.PointingHandCursor)
        bb.setStyleSheet("background: #1A1A1A; color: white; font-size: 13px; font-weight: bold; border-radius: 4px; border: none;")
        bb.clicked.connect(lambda: self.app.show_page("watchlist"))
        bl.addWidget(bb, alignment=Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(banner)

        cl.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)