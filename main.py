import sys
import json
import os
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QLabel, QVBoxLayout, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from loginPage import AuthPages
from movieTable import MovietablePage
from dashboardCinephile import DashboardPage
from profilePage import ProfilePage
from genreAnalyze import GenreAnalyzePage
from movieDetail import MovieDetailPage
from watchlist import WatchlistPage
from scraper import MovieScraper
from styles import BG_MAIN


class _ScraperSignals(QObject):
    data_ready = pyqtSignal(list)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cinephile App")
        self.resize(1100, 850)
        self.setStyleSheet(f"background-color: {BG_MAIN};")

        self.db_path = "data_film.json"
        self.scraper = MovieScraper()
        self.movie_list: list = []
        self.search_query_pending: str | None = None

        self._signals = _ScraperSignals()
        self._signals.data_ready.connect(self._on_data_ready)

        self._central = QWidget()
        self.setCentralWidget(self._central)

        self._main_layout = QVBoxLayout(self._central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self._main_layout.addWidget(self.stack)

        # AuthPages ditambah ke stack sekali saja (index 0)
        self.auth = AuthPages(None, self)
        self.stack.addWidget(self.auth)

        self._load_local_data()

        active_user = None
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r", encoding="utf-8") as f:
                    active_user = json.load(f).get("active_user")
            except Exception:
                pass

        if active_user:
            self.show_page("dashboard")
        else:
            self.show_page("login")

    # ── Data ──────────────────────────────────────────────────────────────

    def _load_local_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.movie_list = json.load(f)
            except Exception:
                self.movie_list = []

        if not self.movie_list:
            threading.Thread(target=self._initialize_data, daemon=True).start()

    def _initialize_data(self):
        hasil = self.scraper.scrape_top_movies()
        if hasil:
            self._signals.data_ready.emit(hasil)

    def _on_data_ready(self, data: list):
        self.movie_list = data
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.movie_list, f, indent=4)
            print("✅ Database Ready!")
        except Exception as e:
            print(f"Gagal menyimpan data: {e}")

    # ── Navigasi ──────────────────────────────────────────────────────────

    def _clear_dynamic_pages(self):
        """Hapus semua widget KECUALI self.auth (index 0)."""
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def show_page(self, page_name: str, data=None):
        self._clear_dynamic_pages()

        # Halaman auth: render_* isi ulang self.auth, lalu tampilkan
        if page_name == "login":
            self.resize(1100, 850)
            self.auth.render_login()
            self.stack.setCurrentWidget(self.auth)
            return

        if page_name == "register":
            self.auth.render_register()
            self.stack.setCurrentWidget(self.auth)
            return

        if page_name == "forgot_password":
            self.auth.render_forgot_password()
            self.stack.setCurrentWidget(self.auth)
            return

        # Halaman lain: buat widget baru
        if page_name == "dashboard":
            self.resize(1100, 850)
            page = DashboardPage(None, self)
        elif page_name == "profile":
            self.resize(1100, 850)
            page = ProfilePage(None, self)
        elif page_name == "movietable":
            page = MovietablePage(None, self)
        elif page_name == "genreanalyze":
            page = GenreAnalyzePage(None, self)
        elif page_name == "moviedetail":
            page = MovieDetailPage(None, self, movie_data=data)
        elif page_name == "watchlist":
            page = WatchlistPage(None, self)
        else:
            return

        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    # ── Toast ─────────────────────────────────────────────────────────────

    def show_toast(self, message: str, target: str | None = None):
        print(f"Toast: {message}")
        if target:
            self.show_page(target)

    # ── Welcome animation ─────────────────────────────────────────────────

    def show_welcome_transition(self, username: str):
        self._clear_dynamic_pages()

        welcome_widget = QWidget()
        welcome_widget.setStyleSheet(f"background-color: {BG_MAIN};")
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(f"Welcome back,\n{username}")
        lbl.setFont(QFont("Arial Black", 46, QFont.Weight.Bold))
        lbl.setStyleSheet("color: white;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        effect = QGraphicsOpacityEffect(lbl)
        lbl.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        self._fade_anim = QPropertyAnimation(effect, b"opacity")
        self._fade_anim.setDuration(800)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.start()

        self.stack.addWidget(welcome_widget)
        self.stack.setCurrentWidget(welcome_widget)

        QTimer.singleShot(2000, self._go_to_dashboard)

    def _go_to_dashboard(self):
        self.show_page("dashboard")

    # ── Search ────────────────────────────────────────────────────────────

    def handle_local_search(self, query: str):
        if not query:
            return
        self.search_query_pending = query.lower().strip()
        self.show_page("movietable")

    # ── Cleanup ───────────────────────────────────────────────────────────

    def closeEvent(self, event):
        try:
            self.scraper.close()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
