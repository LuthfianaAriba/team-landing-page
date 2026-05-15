import sys
import json
import os
import threading

from PyQt6 import QtWidgets, QtCore

from loginPage import AuthPages
from movieTable import MovietablePage
from dashboardCinephile import DashboardPage
from genreAnalyze import GenreAnalyzePage
from movieDetail import MovieDetailPage
from watchlist import WatchlistPage
from scraper import MovieScraper


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cinephile App")
        self.resize(1100, 850)
        self.setStyleSheet("background-color: #1A1A1A;")

        # Variabel sistem
        self.search_query_pending = None
        self.movie_list = []
        self.db_path = "data_film.json"
        self.scraper = MovieScraper()
        self.current_page_instance = None

        # Container utama pakai QStackedWidget
        self.container = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.container)

        # Load data lokal
        self._load_local_data()

        # Init Auth
        self.auth = AuthPages(self.container, self)

        # Cek sesi
        active_user = self.auth.db.get_session()
        if active_user:
            self.show_page("dashboard")
        else:
            self.show_page("login")

    def _load_local_data(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                try:
                    self.movie_list = json.load(f)
                except Exception:
                    self.movie_list = []

        if not self.movie_list:
            print("⚠️ Database kosong. Scraping data awal...")
            threading.Thread(target=self._initialize_data, daemon=True).start()

    def _initialize_data(self):
        hasil = self.scraper.scrape_top_movies()
        if hasil:
            self.movie_list = hasil
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.movie_list, f, indent=4)
            print("✅ Database Ready!")

    def show_page(self, page_name, data=None):
        # Hapus semua widget lama dari stacked widget
        while self.container.count():
            widget = self.container.widget(0)
            self.container.removeWidget(widget)
            widget.deleteLater()

        if page_name == "login":
            widget = self.auth.render_login()
            self.current_page_instance = self.auth
        elif page_name == "register":
            widget = self.auth.render_register()
            self.current_page_instance = self.auth
        elif page_name == "dashboard":
            widget = DashboardPage(self.container, self)
            self.current_page_instance = widget
        elif page_name == "movietable":
            widget = MovietablePage(self.container, self)
            self.current_page_instance = widget
        elif page_name == "genreanalyze":
            widget = GenreAnalyzePage(self.container, self)
            self.current_page_instance = widget
        elif page_name == "moviedetail":
            widget = MovieDetailPage(self.container, self, movie_data=data)
            self.current_page_instance = widget
        elif page_name == "watchlist":
            widget = WatchlistPage(self.container, self)
            self.current_page_instance = widget
        else:
            return

        self.container.addWidget(widget)
        self.container.setCurrentWidget(widget)

    def show_toast(self, message, target=None):
        print(f"🔔 {message}")
        # Pakai QMessageBox sebagai pengganti toast, atau bisa custom SnackBar
        toast = QtWidgets.QMessageBox(self)
        toast.setWindowTitle("Info")
        toast.setText(message)
        toast.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        toast.exec()
        if target:
            self.show_page(target)

    def handle_local_search(self, query):
        if not query:
            return
        query = query.lower().strip()

        if self.current_page_instance.__class__.__name__ == "MovietablePage":
            self.current_page_instance.filter_data(query)
        else:
            self.search_query_pending = query
            self.show_page("movietable")

    def logout(self):
        """Dipanggil dari ProfileWidget saat user logout."""
        try:
            if os.path.exists("session.json"):
                os.remove("session.json")
        except Exception:
            pass
        self.show_page("login")

    def closeEvent(self, event):
        try:
            self.scraper.close()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())