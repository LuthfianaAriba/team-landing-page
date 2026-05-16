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

# Import halaman-halaman aplikasi (sesuaikan nama modul dengan versi PyQt6-nya)
from loginPage import AuthPages
from movieTable import MovietablePage
from dashboardCinephile import DashboardPage
from profilePage import ProfilePage
from genreAnalyze import GenreAnalyzePage
from movieDetail import MovieDetailPage
from watchlist import WatchlistPage
from scraper import MovieScraper
from styles import BG_MAIN  # pastikan styles.py menyediakan konstanta warna dalam format hex string


# ──────────────────────────────────────────────
# Helper: emit sinyal dari thread sekunder
# ──────────────────────────────────────────────
class _ScraperSignals(QObject):
    """Sinyal yang aman dipakai dari background thread."""
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

        # Sinyal dari thread scraper
        self._signals = _ScraperSignals()
        self._signals.data_ready.connect(self._on_data_ready)

        # Widget utama & stacked layout
        self._central = QWidget()
        self.setCentralWidget(self._central)

        self._main_layout = QVBoxLayout(self._central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # QStackedWidget sebagai pengganti container CTk
        self.stack = QStackedWidget()
        self._main_layout.addWidget(self.stack)

        # Auth pages
        self.auth = AuthPages(self.stack, self)

        self._load_local_data()

        # Cek sesi aktif
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

    # ──────────────────────────────────────────
    # Data
    # ──────────────────────────────────────────

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
        """Dipanggil di main thread setelah scraping selesai."""
        self.movie_list = data
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.movie_list, f, indent=4)
            print("✅ Database Ready!")
        except Exception as e:
            print(f"Gagal menyimpan data: {e}")

    # ──────────────────────────────────────────
    # Navigasi halaman
    # ──────────────────────────────────────────

    def _clear_stack(self):
        """Hapus semua widget dari stack kecuali yang sedang ditampilkan."""
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def show_page(self, page_name: str, data=None):
        self._clear_stack()

        if page_name == "login":
            self.resize(1100, 850)
            page = self.auth.render_login()
        elif page_name == "register":
            page = self.auth.render_register()
        elif page_name == "dashboard":
            self.resize(1100, 850)
            page = DashboardPage(self.stack, self)
        elif page_name == "profile":
            self.resize(1100, 850)
            page = ProfilePage(self.stack, self)
        elif page_name == "movietable":
            page = MovietablePage(self.stack, self)
        elif page_name == "genreanalyze":
            page = GenreAnalyzePage(self.stack, self)
        elif page_name == "moviedetail":
            page = MovieDetailPage(self.stack, self, movie_data=data)
        elif page_name == "watchlist":
            page = WatchlistPage(self.stack, self)
        else:
            return

        if page is not None:
            self.stack.addWidget(page)
            self.stack.setCurrentWidget(page)

    # ──────────────────────────────────────────
    # Toast / notifikasi
    # ──────────────────────────────────────────

    def show_toast(self, message: str, target: str | None = None):
        print(f"Toast Notification: {message}")
        if target:
            self.show_page(target)

    # ──────────────────────────────────────────
    # Animasi welcome
    # ──────────────────────────────────────────

    def show_welcome_transition(self, username: str):
        self._clear_stack()

        # Buat frame welcome
        welcome_widget = QWidget()
        welcome_widget.setStyleSheet(f"background-color: {BG_MAIN};")
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(f"Welcome back,\n{username}")
        lbl.setFont(QFont("Arial Black", 46, QFont.Weight.Bold))
        lbl.setStyleSheet("color: white;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        # Fade-in menggunakan QGraphicsOpacityEffect + QPropertyAnimation
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

        # Setelah 2 detik, pindah ke dashboard
        QTimer.singleShot(2000, self._go_to_dashboard)

    def _go_to_dashboard(self):
        self.show_page("dashboard")

    # ──────────────────────────────────────────
    # Search lokal
    # ──────────────────────────────────────────

    def handle_local_search(self, query: str):
        if not query:
            return
        self.search_query_pending = query.lower().strip()
        self.show_page("movietable")

    # ──────────────────────────────────────────
    # Cleanup saat tutup
    # ──────────────────────────────────────────

    def closeEvent(self, event):
        try:
            self.scraper.close()
        except Exception:
            pass
        event.accept()


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
