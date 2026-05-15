import os
from collections import Counter
from PyQt6 import QtCore, QtGui, QtWidgets
from PIL import Image


BG_MAIN    = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#AAAAAA"
ACCENT     = "#E53935"


class GenreAnalyzePage(QtWidgets.QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app

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

        self.setStyleSheet(f"background-color: {BG_MAIN};")
        self.analyzed_data = self._process_genre_logic()

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_nav())

        # Scroll area untuk body
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {BG_MAIN}; }}
            QScrollBar:vertical {{ background: {BG_MAIN}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: #444; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        body_widget = QtWidgets.QWidget()
        body_widget.setStyleSheet(f"background-color: {BG_MAIN};")
        body_layout = QtWidgets.QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        body_layout.addWidget(self._build_hero())
        body_layout.addWidget(self._build_genre_graphics())
        body_layout.addWidget(self._build_top_recommendations())
        body_layout.addWidget(self._build_orange_banner())
        body_layout.addWidget(self._build_footer())

        self._scroll.setWidget(body_widget)
        root_layout.addWidget(self._scroll)

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _load_image(self, path, size):
        key = (path, size)
        if key not in self.app._img_cache:
            pil_img = Image.open(path).resize(size)
            pil_img = pil_img.convert("RGBA")
            data = pil_img.tobytes("raw", "RGBA")
            qimg = QtGui.QImage(data, size[0], size[1], QtGui.QImage.Format.Format_RGBA8888)
            self.app._img_cache[key] = QtGui.QPixmap.fromImage(qimg)
        return self.app._img_cache[key]

    def _process_genre_logic(self):
        all_genres = []
        for movie in getattr(self.app, "movie_list", []):
            raw = movie.get("genre", "Unknown")
            if raw and raw not in ["Unknown", "N/A"]:
                all_genres.extend([g.strip() for g in raw.split(",")])
        counts = Counter(all_genres)
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)

    def _get_genre_description(self, name):
        return self.GENRE_DESCRIPTIONS.get(
            name,
            f"Discover our top recommendations for the {name} genre based on your collection."
        )

    def _label(self, text, size=13, bold=False, italic=False, color=TEXT_WHITE,
               align=QtCore.Qt.AlignmentFlag.AlignLeft, wrap=0, family="Trebuchet MS"):
        lbl = QtWidgets.QLabel(text)
        weight = "bold" if bold else "normal"
        style_str = "italic" if italic else "normal"
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-family: '{family}';
                font-size: {size}px;
                font-weight: {weight};
                font-style: {style_str};
                background: transparent;
            }}
        """)
        lbl.setAlignment(align)
        if wrap:
            lbl.setWordWrap(True)
            lbl.setMaximumWidth(wrap)
        return lbl

    # ── NAV ───────────────────────────────────────────────────────────────────
    def _build_nav(self):
        nav = QtWidgets.QWidget()
        nav.setFixedHeight(60)
        nav.setStyleSheet("background-color: #111111;")

        layout = QtWidgets.QHBoxLayout(nav)
        layout.setContentsMargins(20, 0, 20, 0)

        # Pills center
        pill = QtWidgets.QWidget()
        pill.setStyleSheet("background-color: #2E2E2E; border-radius: 20px;")
        pill_layout = QtWidgets.QHBoxLayout(pill)
        pill_layout.setContentsMargins(6, 3, 6, 3)
        pill_layout.setSpacing(2)

        nav_items = [
            ("Home",           "dashboard",    False),
            ("Genre Analysis", "genreanalyze", True),
            ("Movie Table",    "movietable",   False),
            ("Watchlist",      "watchlist",    False),
        ]
        for label, page, active in nav_items:
            btn = QtWidgets.QPushButton(label)
            btn.setFixedHeight(28)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {ACCENT}; color: white;
                        border-radius: 16px; font-family: 'Trebuchet MS';
                        font-size: 11px; font-weight: bold; border: none; padding: 0 12px; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: transparent; color: {TEXT_GRAY};
                        border-radius: 16px; font-family: 'Trebuchet MS';
                        font-size: 11px; font-weight: bold; border: none; padding: 0 12px; }}
                    QPushButton:hover {{ background-color: #3E3E3E; color: white; }}
                """)
                p = page
                btn.clicked.connect(lambda _, pg=p: self.app.show_page(pg))
            pill_layout.addWidget(btn)

        # Search right
        search_w = QtWidgets.QWidget()
        search_w.setStyleSheet("background: transparent;")
        sl = QtWidgets.QHBoxLayout(search_w)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(5)

        self.search_entry = QtWidgets.QLineEdit()
        self.search_entry.setPlaceholderText("Search Local...")
        self.search_entry.setFixedSize(150, 32)
        self.search_entry.setStyleSheet("""
            QLineEdit { background-color: #222; color: white; border: 1px solid #444;
                border-radius: 4px; padding: 0 8px; font-size: 12px; }
        """)
        self.search_entry.returnPressed.connect(
            lambda: self.app.handle_local_search(self.search_entry.text())
        )

        search_btn = QtWidgets.QPushButton("🔍")
        search_btn.setFixedSize(40, 32)
        search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background-color: #c0392b; }}
        """)
        search_btn.clicked.connect(
            lambda: self.app.handle_local_search(self.search_entry.text())
        )

        sl.addWidget(self.search_entry)
        sl.addWidget(search_btn)

        layout.addWidget(pill, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(search_w)

        return nav

    # ── HERO ──────────────────────────────────────────────────────────────────
    def _build_hero(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet(f"background-color: {BG_MAIN};")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(150, 60, 150, 40)
        layout.setSpacing(0)

        title = self._label("Genre Analyze", size=70, bold=True,
                            family="Helvetica",
                            align=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(20)

        # Deco color blocks
        deco = QtWidgets.QWidget()
        deco.setStyleSheet("background: transparent;")
        deco_layout = QtWidgets.QHBoxLayout(deco)
        deco_layout.setContentsMargins(0, 0, 0, 0)
        deco_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        for color in ["#2d5a27", "#333333", "#c4a484", "#555555"]:
            block = QtWidgets.QWidget()
            block.setFixedSize(120, 90)
            block.setStyleSheet(f"background-color: {color}; border-radius: 8px;")
            deco_layout.addWidget(block)
            deco_layout.addSpacing(15)
        layout.addWidget(deco)
        layout.addSpacing(40)

        # Overview row
        overview_row = QtWidgets.QWidget()
        overview_row.setStyleSheet("background: transparent;")
        ov_layout = QtWidgets.QHBoxLayout(overview_row)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.setSpacing(40)

        ov_layout.addWidget(
            self._label("OVERVIEW", size=12, bold=True, color=TEXT_GRAY),
            alignment=QtCore.Qt.AlignmentFlag.AlignTop
        )

        overview_text = (
            "Genre Analysis helps you understand your cinematic preferences by examining the "
            "distribution of genres in your collection. It highlights which genres appear most "
            "frequently, providing insights through an easy-to-read graphical interface."
        )
        ov_lbl = self._label(overview_text, size=13, color=TEXT_WHITE, wrap=600)
        ov_layout.addWidget(ov_lbl)
        ov_layout.addStretch()

        layout.addWidget(overview_row)

        return widget

    # ── GENRE GRAPHICS ────────────────────────────────────────────────────────
    def _build_genre_graphics(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet(f"background-color: {BG_MAIN};")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(150, 20, 150, 20)
        layout.setSpacing(4)

        layout.addWidget(
            self._label("Genre Distribution", size=35, italic=True,
                        family="Georgia", align=QtCore.Qt.AlignmentFlag.AlignCenter),
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        layout.addSpacing(20)

        top_10 = self.analyzed_data[:10]
        if not top_10:
            layout.addWidget(self._label("No movie data available.", color=TEXT_GRAY))
            return widget

        max_val = top_10[0][1]

        for genre, count in top_10:
            row = QtWidgets.QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)

            lbl = self._label(f"{genre} ({count})", size=12, bold=True)
            lbl.setFixedWidth(140)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(lbl)

            bar_w = max(5, int((count / max_val) * 400))
            bar = QtWidgets.QWidget()
            bar.setFixedSize(bar_w, 20)
            bar.setStyleSheet(f"background-color: {ACCENT}; border-radius: 2px;")
            row_layout.addWidget(bar)
            row_layout.addStretch()

            layout.addWidget(row)

        return widget

    # ── TOP RECOMMENDATIONS ───────────────────────────────────────────────────
    def _build_top_recommendations(self):
        widget = QtWidgets.QWidget()
        widget.setStyleSheet(f"background-color: {BG_MAIN};")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(150, 0, 150, 0)
        layout.setSpacing(0)

        top_3 = self.analyzed_data[:3]
        movie_list = getattr(self.app, "movie_list", [])

        for index, (name, count) in enumerate(top_3):
            layout.addSpacing(40)

            layout.addWidget(self._label(name, size=32, bold=True, family="Helvetica"))
            layout.addSpacing(10)
            layout.addWidget(self._label(self._get_genre_description(name),
                                         size=13, color=TEXT_GRAY, wrap=650))
            layout.addSpacing(15)
            layout.addWidget(self._label(f"Featured {name} Titles", size=12, bold=True))
            layout.addSpacing(15)

            # Poster row
            poster_row = QtWidgets.QWidget()
            poster_row.setStyleSheet("background: transparent;")
            pr_layout = QtWidgets.QHBoxLayout(poster_row)
            pr_layout.setContentsMargins(0, 0, 0, 0)
            pr_layout.setSpacing(20)
            pr_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

            matching = [
                m for m in movie_list
                if name in [g.strip() for g in m.get("genre", "").split(",")]
            ]

            for m_data in matching[:4]:
                path = m_data.get("poster_local", "")
                if path and os.path.exists(path):
                    try:
                        pixmap = self._load_image(path, (130, 190))
                        lbl = QtWidgets.QLabel()
                        lbl.setPixmap(pixmap)
                        lbl.setFixedSize(130, 190)
                        lbl.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
                        lbl.mousePressEvent = lambda e, d=m_data: self.app.show_page("moviedetail", data=d)
                        pr_layout.addWidget(lbl)
                        continue
                    except Exception:
                        pass

                # Fallback placeholder
                placeholder = QtWidgets.QWidget()
                placeholder.setFixedSize(130, 190)
                placeholder.setStyleSheet("background-color: #333333; border-radius: 4px;")
                ph_layout = QtWidgets.QVBoxLayout(placeholder)
                ph_lbl = self._label(m_data.get("title", "No Title"), size=11,
                                     color=TEXT_WHITE, wrap=110)
                ph_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                ph_layout.addWidget(ph_lbl)
                pr_layout.addWidget(placeholder)

            pr_layout.addStretch()
            layout.addWidget(poster_row)

            if index < len(top_3) - 1:
                layout.addSpacing(20)
                sep = QtWidgets.QFrame()
                sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                sep.setStyleSheet("color: #333333; background-color: #333333;")
                sep.setFixedHeight(1)
                layout.addWidget(sep)

        layout.addSpacing(40)
        return widget

    # ── ORANGE BANNER ─────────────────────────────────────────────────────────
    def _build_orange_banner(self):
        banner = QtWidgets.QWidget()
        banner.setFixedHeight(180)
        banner.setStyleSheet("background-color: #FF8C00;")

        layout = QtWidgets.QVBoxLayout(banner)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        layout.addWidget(
            self._label("Ready for a movie marathon?", size=32, italic=True,
                        family="Georgia", color="#111111",
                        align=QtCore.Qt.AlignmentFlag.AlignCenter)
        )
        layout.addSpacing(5)
        layout.addWidget(
            self._label("Review your watchlist and plan your next cinematic journey.",
                        size=14, color="#222222",
                        align=QtCore.Qt.AlignmentFlag.AlignCenter)
        )
        layout.addSpacing(20)

        btn = QtWidgets.QPushButton("Open Watchlist")
        btn.setFixedSize(160, 40)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #111111; color: white;
                border: none; border-radius: 0px;
                font-family: 'Trebuchet MS'; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #333333; }
        """)
        btn.clicked.connect(lambda: self.app.show_page("watchlist"))
        layout.addWidget(btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        return banner

    # ── FOOTER ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        footer = QtWidgets.QWidget()
        footer.setFixedHeight(150)
        footer.setStyleSheet("background-color: #0A0A0A;")

        layout = QtWidgets.QHBoxLayout(footer)
        layout.setContentsMargins(40, 0, 40, 0)

        layout.addWidget(
            self._label("Cinephile", size=50, bold=True, family="Helvetica"),
            alignment=QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft
        )
        layout.addStretch()
        layout.addWidget(
            self._label(
                "©2026 Cinephile Archive\nCurating cinematic excellence for your personal collection.",
                size=11, color=TEXT_GRAY,
                align=QtCore.Qt.AlignmentFlag.AlignRight
            ),
            alignment=QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight
        )

        return footer