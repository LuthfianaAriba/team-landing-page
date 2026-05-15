import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PIL import Image


BG_MAIN    = "#1A1A1A"
BG_LIGHT   = "#F4F4F4"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#AAAAAA"
ACCENT     = "#E53935"


class MovietablePage(QtWidgets.QWidget):
    def __init__(self, parent=None, app=None, genre_filter=None):
        super().__init__(parent)
        self.app = app
        self.current_page = 0
        self.items_per_page = 20
        self.sort_key = "default"

        self.all_movies = getattr(self.app, "movie_list", [])
        self.filtered_list = self.all_movies.copy()
        self._genre_selected = set()

        self.setStyleSheet(f"background-color: {BG_MAIN};")

        self._build_ui()

        if genre_filter:
            QtCore.QTimer.singleShot(100, lambda: self._toggle_genre(genre_filter))
        else:
            pending = getattr(self.app, "search_query_pending", None)
            if pending:
                self.app.search_query_pending = None
                QtCore.QTimer.singleShot(100, lambda: self._search(pending))

    # ── SORT ──────────────────────────────────────────────────────────────────
    def _apply_sort(self, data):
        if self.sort_key == "title":
            return sorted(data, key=lambda m: m.get("title", "").lower())
        elif self.sort_key == "year_desc":
            return sorted(data, key=lambda m: m.get("year", "0"), reverse=True)
        elif self.sort_key == "year_asc":
            return sorted(data, key=lambda m: m.get("year", "0"))
        elif self.sort_key == "rating_desc":
            return sorted(data, key=lambda m: float(m.get("rating", 0) or 0), reverse=True)
        elif self.sort_key == "rating_asc":
            return sorted(data, key=lambda m: float(m.get("rating", 0) or 0))
        elif self.sort_key == "genre":
            return sorted(data, key=lambda m: m.get("genre", "").lower())
        return data

    # ── FILTER ────────────────────────────────────────────────────────────────
    def _apply_filters(self):
        if hasattr(self, "_filter_timer"):
            self._filter_timer.stop()
        self._filter_timer = QtCore.QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._do_apply_filters)
        self._filter_timer.start(120)

    def _do_apply_filters(self):
        self.current_page = 0
        all_data = getattr(self.app, "movie_list", [])

        if self._genre_selected:
            filtered = []
            for m in all_data:
                film_genres = {g.strip() for g in str(m.get("genre", "")).split(",")}
                if self._genre_selected.issubset(film_genres):
                    filtered.append(m)
        else:
            filtered = all_data.copy()

        q = self.search_entry.text().lower().strip() if hasattr(self, "search_entry") else ""
        if q:
            filtered = [m for m in filtered
                        if q in str(m.get("title", "")).lower()
                        or q in str(m.get("genre", "")).lower()]

        self.filtered_list = self._apply_sort(filtered)
        self.render_table()

    def _search(self, query):
        self._apply_filters()

    def _toggle_genre(self, genre):
        if genre in self._genre_selected:
            self._genre_selected.discard(genre)
        else:
            self._genre_selected.add(genre)
        self._refresh_genre_label()
        self._apply_filters()

    def _clear_genres(self):
        self._genre_selected.clear()
        self._refresh_genre_label()
        self._apply_filters()

    def _refresh_genre_label(self):
        if self._genre_selected:
            label_text = ", ".join(sorted(self._genre_selected))
            if len(label_text) > 40:
                label_text = label_text[:37] + "..."
            self._genre_label.setText(label_text)
            self._genre_label.setStyleSheet(f"color: {TEXT_WHITE}; background: transparent;")
            self._genre_btn_main.setStyleSheet(self._btn_style(active=True))
        else:
            self._genre_label.setText("All genres")
            self._genre_label.setStyleSheet(f"color: {TEXT_GRAY}; background: transparent;")
            self._genre_btn_main.setStyleSheet(self._btn_style(active=False))

    def _set_sort(self, key):
        self.sort_key = key
        self.current_page = 0
        self.filtered_list = self._apply_sort(self.filtered_list)
        self.render_table()
        self._refresh_sort_buttons()

    def _refresh_sort_buttons(self):
        for k, btn in self._sort_buttons.items():
            if k == self.sort_key:
                btn.setStyleSheet(self._sort_btn_style(active=True))
            else:
                btn.setStyleSheet(self._sort_btn_style(active=False))

    # ── STYLES ────────────────────────────────────────────────────────────────
    def _btn_style(self, active=False):
        bg = ACCENT if active else "#2E2E2E"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {TEXT_WHITE};
                border-radius: 16px;
                font-family: 'Trebuchet MS';
                font-size: 11px;
                font-weight: bold;
                border: none;
                padding: 4px 12px;
            }}
            QPushButton:hover {{ background-color: {'#c0392b' if active else '#3E3E3E'}; }}
        """

    def _sort_btn_style(self, active=False):
        bg = ACCENT if active else "#2E2E2E"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {TEXT_WHITE if active else TEXT_GRAY};
                border-radius: 14px;
                font-family: 'Trebuchet MS';
                font-size: 11px;
                font-weight: bold;
                border: none;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background-color: {'#c0392b' if active else '#3E3E3E'}; }}
        """

    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_nav())
        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_filter_row())
        root_layout.addWidget(self._build_table_area(), stretch=1)
        root_layout.addWidget(self._build_pagination())

    def _build_nav(self):
        nav = QtWidgets.QWidget()
        nav.setFixedHeight(60)
        nav.setStyleSheet("background-color: #111111;")

        layout = QtWidgets.QHBoxLayout(nav)
        layout.setContentsMargins(20, 0, 20, 0)

        # Nav pills (center)
        pill = QtWidgets.QWidget()
        pill.setStyleSheet("background-color: #2E2E2E; border-radius: 20px;")
        pill_layout = QtWidgets.QHBoxLayout(pill)
        pill_layout.setContentsMargins(6, 3, 6, 3)
        pill_layout.setSpacing(2)

        nav_buttons = [
            ("Home",           "dashboard",    False),
            ("Genre Analysis", "genreanalyze", False),
            ("Movie Table",    "movietable",   True),
            ("Watchlist",      "watchlist",    False),
        ]
        for label, page, active in nav_buttons:
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
            if not active:
                p = page
                btn.clicked.connect(lambda _, pg=p: self.app.show_page(pg))
            pill_layout.addWidget(btn)

        # Search (right)
        search_widget = QtWidgets.QWidget()
        search_widget.setStyleSheet("background: transparent;")
        search_layout = QtWidgets.QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(5)

        self.search_entry = QtWidgets.QLineEdit()
        self.search_entry.setPlaceholderText("Search...")
        self.search_entry.setFixedSize(150, 32)
        self.search_entry.setStyleSheet("""
            QLineEdit { background-color: #222; color: white; border: 1px solid #444;
                border-radius: 4px; padding: 0 8px; font-size: 12px; }
        """)
        self.search_entry.returnPressed.connect(lambda: self._search(self.search_entry.text()))

        search_btn = QtWidgets.QPushButton("🔍")
        search_btn.setFixedSize(40, 32)
        search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background-color: #c0392b; }}
        """)
        search_btn.clicked.connect(lambda: self._search(self.search_entry.text()))

        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(search_btn)

        layout.addWidget(pill, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(search_widget)

        return nav

    def _build_header(self):
        header = QtWidgets.QLabel("Find your movie!")
        header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel { color: white; font-family: Georgia; font-size: 38px;
                font-weight: bold; background: transparent; padding: 20px 0 8px 0; }
        """)
        return header

    def _build_filter_row(self):
        row = QtWidgets.QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(40, 0, 40, 10)
        layout.setSpacing(0)

        # Genre button
        self._genre_btn_main = QtWidgets.QPushButton("Genre ▼")
        self._genre_btn_main.setFixedSize(100, 32)
        self._genre_btn_main.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self._genre_btn_main.setStyleSheet(self._btn_style(active=False))
        self._genre_btn_main.clicked.connect(self._show_genre_menu)
        layout.addWidget(self._genre_btn_main)
        layout.addSpacing(12)

        # Genre label
        self._genre_label = QtWidgets.QLabel("All genres")
        self._genre_label.setStyleSheet(f"color: {TEXT_GRAY}; font-family: 'Trebuchet MS'; font-size: 11px; background: transparent;")
        layout.addWidget(self._genre_label)
        layout.addSpacing(20)

        # Divider
        div = QtWidgets.QFrame()
        div.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        div.setFixedHeight(24)
        div.setStyleSheet("color: #444;")
        layout.addWidget(div)
        layout.addSpacing(12)

        # Sort label
        sort_lbl = QtWidgets.QLabel("Sort :")
        sort_lbl.setStyleSheet(f"color: {TEXT_GRAY}; font-family: 'Trebuchet MS'; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(sort_lbl)
        layout.addSpacing(8)

        # Sort buttons
        self._sort_buttons = {}
        sort_options = [
            ("Default",   "default"),
            ("A–Z Title", "title"),
            ("Newest",    "year_desc"),
            ("Oldest",    "year_asc"),
            ("Rating ↓",  "rating_desc"),
            ("Rating ↑",  "rating_asc"),
        ]
        for label, key in sort_options:
            btn = QtWidgets.QPushButton(label)
            btn.setFixedHeight(28)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._sort_btn_style(active=(key == self.sort_key)))
            btn.clicked.connect(lambda _, k=key: self._set_sort(k))
            layout.addWidget(btn)
            layout.addSpacing(3)
            self._sort_buttons[key] = btn

        layout.addStretch()

        # Count label
        self._count_label = QtWidgets.QLabel("")
        self._count_label.setStyleSheet(f"color: {TEXT_GRAY}; font-family: 'Trebuchet MS'; font-size: 11px; background: transparent;")
        layout.addWidget(self._count_label)

        return row

    def _show_genre_menu(self):
        """Dropdown genre pakai QMenu."""
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #222222; border: 1px solid #444; border-radius: 8px; padding: 4px; }
            QMenu::item { color: #AAAAAA; padding: 6px 20px; font-family: 'Trebuchet MS'; font-size: 11px; }
            QMenu::item:selected { background-color: #3E3E3E; color: white; }
            QMenu::item:checked { color: #E53935; font-weight: bold; }
        """)

        # Clear all action
        clear_action = menu.addAction("✕ Clear All")
        clear_action.triggered.connect(self._clear_genres)
        menu.addSeparator()

        # Genre actions
        all_genres = set()
        for m in self.all_movies:
            for g in str(m.get("genre", "")).split(","):
                g = g.strip()
                if g:
                    all_genres.add(g)

        for genre in sorted(all_genres):
            action = menu.addAction(f"{'✓ ' if genre in self._genre_selected else '   '}{genre}")
            action.triggered.connect(lambda _, g=genre: self._toggle_genre(g))

        menu.exec(self._genre_btn_main.mapToGlobal(
            QtCore.QPoint(0, self._genre_btn_main.height() + 4)
        ))

    def _build_table_area(self):
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"background-color: {BG_MAIN}; border-radius: 15px;")
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(40, 10, 40, 0)

        # Scroll area
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1A1A1A; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #444; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self._grid_widget = QtWidgets.QWidget()
        self._grid_widget.setStyleSheet("background: transparent;")
        self._grid_layout = QtWidgets.QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(6, 6, 6, 6)

        self._scroll_area.setWidget(self._grid_widget)
        layout.addWidget(self._scroll_area)

        return container

    def _build_pagination(self):
        self._pagination_widget = QtWidgets.QWidget()
        self._pagination_widget.setStyleSheet("background: transparent;")
        layout = QtWidgets.QHBoxLayout(self._pagination_widget)
        layout.setContentsMargins(40, 10, 40, 15)

        self._prev_btn = QtWidgets.QPushButton("◀ Prev")
        self._prev_btn.setFixedSize(100, 34)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; border: none;
                border-radius: 4px; font-family: 'Trebuchet MS'; font-weight: bold; }}
            QPushButton:hover {{ background-color: #c0392b; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
        """)
        self._prev_btn.clicked.connect(self.prev_page)

        self._page_label = QtWidgets.QLabel("Page 1 of 1")
        self._page_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet(f"color: {TEXT_WHITE}; font-family: 'Trebuchet MS'; background: transparent;")

        self._next_btn = QtWidgets.QPushButton("Next ▶")
        self._next_btn.setFixedSize(100, 34)
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self.next_page)

        layout.addWidget(self._prev_btn)
        layout.addStretch()
        layout.addWidget(self._page_label)
        layout.addStretch()
        layout.addWidget(self._next_btn)

        return self._pagination_widget

    # ── RENDER TABLE ──────────────────────────────────────────────────────────
    def render_table(self):
        # Bersihkan grid
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._scroll_area.verticalScrollBar().setValue(0)

        COLS = 5
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        movies_to_show = self.filtered_list[start:end]
        total = len(self.filtered_list)
        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)

        genre_info = f"  •  {len(self._genre_selected)} genre selected" if self._genre_selected else ""
        self._count_label.setText(f"{total} films{genre_info}")

        if not movies_to_show:
            empty_lbl = QtWidgets.QLabel("No movies found. 😔")
            empty_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #888888; font-size: 14px; background: transparent;")
            self._grid_layout.addWidget(empty_lbl, 0, 0, 1, COLS)
        else:
            self._poster_refs = []  # Cegah garbage collection

            for idx, movie in enumerate(movies_to_show):
                row_i = idx // COLS
                col_i = idx % COLS
                card = self._make_card(movie)
                self._grid_layout.addWidget(card, row_i, col_i,
                                             QtCore.Qt.AlignmentFlag.AlignTop)

        # Update pagination
        self._prev_btn.setEnabled(self.current_page > 0)
        self._next_btn.setEnabled(end < len(self.filtered_list))
        self._page_label.setText(f"Page {self.current_page + 1} of {total_pages}")

    def _make_card(self, movie):
        POSTER_W, POSTER_H = 160, 220

        card = QtWidgets.QWidget()
        card.setFixedWidth(POSTER_W + 16)
        card.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        card.setStyleSheet("""
            QWidget#movieCard {
                background-color: #2E2E2E;
                border-radius: 10px;
                border: 1px solid #444;
            }
        """)
        card.setObjectName("movieCard")

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Poster
        poster_lbl = QtWidgets.QLabel()
        poster_lbl.setFixedSize(POSTER_W, POSTER_H)
        poster_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        poster_lbl.setStyleSheet("background-color: #1A1A1A; border-radius: 8px; color: #888; font-size: 32px;")
        poster_lbl.setText("🎬")

        path = movie.get("poster_local", "")
        if path and os.path.exists(path):
            try:
                pil_img = Image.open(path).resize((POSTER_W, POSTER_H))
                pil_img = pil_img.convert("RGBA")
                data = pil_img.tobytes("raw", "RGBA")
                qimg = QtGui.QImage(data, POSTER_W, POSTER_H, QtGui.QImage.Format.Format_RGBA8888)
                pixmap = QtGui.QPixmap.fromImage(qimg)
                poster_lbl.setPixmap(pixmap)
                poster_lbl.setText("")
                self._poster_refs.append(pixmap)
            except Exception:
                pass

        layout.addWidget(poster_lbl)

        # Title
        title_lbl = QtWidgets.QLabel(movie.get("title", "Unknown"))
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-family: 'Trebuchet MS'; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(title_lbl)

        # Year & Genre
        sub_lbl = QtWidgets.QLabel(f"{movie.get('year', 'N/A')}  •  {movie.get('genre', 'N/A')}")
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(f"color: {TEXT_GRAY}; font-family: 'Trebuchet MS'; font-size: 10px; background: transparent;")
        layout.addWidget(sub_lbl)

        # Rating
        rating_lbl = QtWidgets.QLabel(f"⭐ {movie.get('rating', 'N/A')}  IMDb")
        rating_lbl.setStyleSheet(f"color: {ACCENT}; font-family: 'Trebuchet MS'; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(rating_lbl)

        # Hover effect
        card.enterEvent = lambda e, c=card: c.setStyleSheet("""
            QWidget#movieCard { background-color: #3D3D3D; border-radius: 10px; border: 2px solid #E53935; }
        """)
        card.leaveEvent = lambda e, c=card: c.setStyleSheet("""
            QWidget#movieCard { background-color: #2E2E2E; border-radius: 10px; border: 1px solid #444; }
        """)
        card.mousePressEvent = lambda e, m=movie: self.app.show_page("moviedetail", data=m)

        return card

    def filter_data(self, query):
        if hasattr(self, "search_entry"):
            self.search_entry.setText(query)
        self._apply_filters()

    def prev_page(self):
        self.current_page -= 1
        self.render_table()

    def next_page(self):
        self.current_page += 1
        self.render_table()