"""
main.py  –  Cinephile App  (PyQt6 port)
=====================================================
Port dari tkinter / customtkinter ke PyQt6.

Dependency:
    pip install PyQt6 Pillow

Modul eksternal yang tetap dipakai:
    loginPage, movieTable, dashboardCinephile, profilePage,
    genreAnalyze, movieDetail, watchlist, scraper
"""

import json
import os
import random
import sys
import threading

from PyQt6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize,
    QThread, Qt, QTimer, pyqtSignal, QObject,
)
from PyQt6.QtGui import (
    QColor, QCursor, QFont, QImage, QLinearGradient,
    QPainter, QPainterPath, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QFrame, QGraphicsOpacityEffect, QLabel,
    QMainWindow, QStackedWidget, QWidget,
)

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ──────────────────────────────────────────────── poster constants
_POSTER_W = 130
_POSTER_H = 195
_N        = 24

_GRID = [
    (0.00, 0.00, 0.6),  (0.00, 0.25, 0.9),  (0.00, 0.50, 0.7),  (0.00, 0.75, 1.0),
    (0.17, 0.12, 1.0),  (0.17, 0.37, 0.55), (0.17, 0.62, 1.05), (0.17, 0.87, 0.8),
    (0.34, 0.00, 0.85), (0.34, 0.25, 1.1),  (0.34, 0.50, 0.65), (0.34, 0.75, 0.9),
    (0.51, 0.12, 1.2),  (0.51, 0.37, 0.8),  (0.51, 0.62, 1.0),  (0.51, 0.87, 0.7),
    (0.68, 0.00, 0.9),  (0.68, 0.25, 1.1),  (0.68, 0.50, 0.75), (0.68, 0.75, 1.0),
    (0.85, 0.12, 0.7),  (0.85, 0.37, 1.0),  (0.85, 0.62, 0.85), (0.85, 0.87, 0.95),
]

_POSTER_CACHE: list = []


# ─────────────────────────────────────────── background poster cache worker
class PosterCacheWorker(QObject):
    done = pyqtSignal(list)

    def __init__(self, movie_list: list):
        super().__init__()
        self.movie_list = movie_list

    def run(self):
        global _POSTER_CACHE
        if not PIL_AVAILABLE:
            self.done.emit([])
            return

        pool = [m for m in self.movie_list
                if m.get("poster_local") and os.path.exists(m["poster_local"])]
        if not pool:
            self.done.emit([])
            return

        random.shuffle(pool)
        while len(pool) < _N:
            pool = pool * 2
        pool = pool[:_N]

        pixmaps = []
        for m in pool:
            try:
                img = Image.open(m["poster_local"]).convert("RGB")
                img = img.resize((_POSTER_W, _POSTER_H), Image.LANCZOS)
                img = img.filter(ImageFilter.GaussianBlur(1.5))
                img = ImageEnhance.Brightness(img).enhance(0.25)
                data = img.tobytes("raw", "RGB")
                qimg = QImage(data, _POSTER_W, _POSTER_H, QImage.Format.Format_RGB888)
                pixmaps.append(QPixmap.fromImage(qimg))
            except Exception:
                px = QPixmap(_POSTER_W, _POSTER_H)
                px.fill(QColor(20, 20, 20))
                pixmaps.append(px)

        _POSTER_CACHE = pixmaps
        self.done.emit(pixmaps)


# ══════════════════════════════════════════════════════ WELCOME SCREEN
class WelcomeScreen(QWidget):
    exit_requested = pyqtSignal()

    def __init__(self, parent, app, username: str):
        super().__init__(parent)
        self.app      = app
        self.username = username
        self.setMouseTracking(True)

        self._posters: list[dict] = []
        self._mouse_x = 0.0
        self._mouse_y = 0.0
        self._smooth_x = 0.0
        self._smooth_y = 0.0
        self._fade_alpha = 0
        self._fading_out = False
        self._fade_step  = 0
        self._btn_rect = QRect(0, 0, 0, 0)
        self._btn_hovered = False

        self._parallax_timer = QTimer(self)
        self._parallax_timer.setInterval(16)
        self._parallax_timer.timeout.connect(self._tick_parallax)
        self._parallax_timer.start()

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(18)
        self._fade_timer.timeout.connect(self._tick_fadeout)

        self._load_posters()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _load_posters(self):
        global _POSTER_CACHE
        if _POSTER_CACHE:
            QTimer.singleShot(50, lambda: self._on_posters_ready(_POSTER_CACHE[:]))
            return

        self._thread = QThread()
        self._worker = PosterCacheWorker(getattr(self.app, "movie_list", []))
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_posters_ready)
        self._worker.done.connect(self._thread.quit)
        self._thread.start()

    def _on_posters_ready(self, pixmaps: list):
        if not pixmaps or not self.isVisible():
            return
        w, h = self.width() or 1100, self.height() or 850
        self._posters.clear()
        for i, px in enumerate(pixmaps[:_N]):
            rx, ry, depth = _GRID[i]
            jx = random.randint(-4, 4)
            jy = random.randint(-4, 4)
            self._posters.append({
                "pixmap": px,
                "base_x": rx * w + jx,
                "base_y": ry * h + jy,
                "rx": rx, "ry": ry, "jx": jx, "jy": jy,
                "depth": depth,
            })
        self.update()

    def _update_layout(self, w, h):
        bw, bh = 230, 48
        bx = w // 2 - bw // 2
        by = int(h * 0.64) - bh // 2
        self._btn_rect = QRect(bx, by, bw, bh)
        for p in self._posters:
            p["base_x"] = p["rx"] * w + p["jx"]
            p["base_y"] = p["ry"] * h + p["jy"]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._smooth_x = self.width() / 2
        self._smooth_y = self.height() / 2
        self._update_layout(self.width(), self.height())

    def mouseMoveEvent(self, event):
        self._mouse_x = float(event.position().x())
        self._mouse_y = float(event.position().y())
        hovered = self._btn_rect.contains(int(self._mouse_x), int(self._mouse_y))
        if hovered != self._btn_hovered:
            self._btn_hovered = hovered
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor
                                   if hovered else Qt.CursorShape.ArrowCursor))
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._btn_rect.contains(event.position().toPoint()):
                self._start_fadeout()

    def _tick_parallax(self):
        ease = 0.07
        self._smooth_x += (self._mouse_x - self._smooth_x) * ease
        self._smooth_y += (self._mouse_y - self._smooth_y) * ease
        self.update()

    def _start_fadeout(self):
        if self._fading_out:
            return
        self._fading_out = True
        self._fade_step  = 0
        self._fade_timer.start()

    def _tick_fadeout(self):
        total = 20
        self._fade_step += 1
        progress = self._fade_step / total
        self._fade_alpha = int(min(255, progress ** 2 * 255 * 1.2))
        self.update()
        if self._fade_step >= total:
            self._fade_timer.stop()
            QTimer.singleShot(60, self.exit_requested.emit)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        painter.fillRect(self.rect(), QColor("#0D0D0D"))

        strip_color = QColor("#1C1C1C")
        hole_color  = QColor("#0D0D0D")
        for x_strip in (0, w - 44):
            painter.fillRect(x_strip, 0, 44, h, strip_color)
            for i in range(120):
                painter.fillRect(x_strip + 15, 10 + i * 36, 14, 9, hole_color)

        if self._posters:
            ox = max(-1.0, min(1.0, (self._smooth_x - cx) / max(cx, 1)))
            oy = max(-1.0, min(1.0, (self._smooth_y - cy) / max(cy, 1)))
            for p in self._posters:
                px = int(p["base_x"] + ox * 30 * p["depth"])
                py = int(p["base_y"] + oy * 20 * p["depth"])
                painter.drawPixmap(px, py, p["pixmap"])

        painter.setPen(QColor("#666666"))
        f_tag = QFont("Trebuchet MS", 11)
        f_tag.setBold(True)
        painter.setFont(f_tag)
        painter.drawText(QRect(0, int(h * 0.33) - 20, w, 40),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         "✦  CINEPHILE  ·  YOUR CINEMA UNIVERSE")

        painter.setPen(QColor("#FFFFFF"))
        f_wb = QFont("Georgia", 42)
        f_wb.setBold(True)
        painter.setFont(f_wb)
        painter.drawText(QRect(0, int(h * 0.40) - 35, w, 70),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         "Welcome back,")

        painter.setPen(QColor("#E8A020"))
        f_user = QFont("Georgia", 50)
        f_user.setBold(True)
        painter.setFont(f_user)
        painter.drawText(QRect(0, int(h * 0.49) - 40, w, 80),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         self.username)

        stats = self._get_stats()
        painter.setPen(QColor("#BBBBBB"))
        f_stats = QFont("Trebuchet MS", 13)
        painter.setFont(f_stats)
        stats_text = (f"{stats['films']} films  ·  "
                      f"{stats['watchlist']} watchlists  ·  "
                      f"{stats['rating']} avg rating")
        painter.drawText(QRect(0, int(h * 0.56) - 20, w, 40),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         stats_text)

        btn_color = QColor("#C62828") if self._btn_hovered else QColor("#b03535")
        path = QPainterPath()
        path.addRoundedRect(
            float(self._btn_rect.x()), float(self._btn_rect.y()),
            float(self._btn_rect.width()), float(self._btn_rect.height()),
            24.0, 24.0,
        )
        painter.fillPath(path, btn_color)

        painter.setPen(QColor("#FFFFFF"))
        f_btn = QFont("Trebuchet MS", 14)
        f_btn.setBold(True)
        painter.setFont(f_btn)
        painter.drawText(self._btn_rect,
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                         "▶   Lanjutkan menonton")

        if self._fade_alpha > 0:
            overlay = QColor(0, 0, 0, min(255, self._fade_alpha))
            painter.fillRect(self.rect(), overlay)

    def _get_stats(self) -> dict:
        films = len(getattr(self.app, "movie_list", []))
        wl = 0
        try:
            if os.path.exists("watchlist.json"):
                with open("watchlist.json") as f:
                    wl = len(json.load(f).get(self.username, []))
        except Exception:
            pass
        return {"films": films or 250, "watchlist": wl or 12, "rating": "4.9"}

    def cleanup(self):
        self._parallax_timer.stop()
        self._fade_timer.stop()


# ══════════════════════════════════════════════════════════════ MAIN APP
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cinephile App")
        self.resize(1100, 850)
        self.setStyleSheet("background-color: #0D0D0D;")

        self.db_path   = "data_film.json"
        self.username  = "guest"
        self.is_admin  = False
        self._welcome  = None
        self._img_cache = {}
        self.search_query_pending = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._load_local_data()

        # Cek sesi aktif
        active_user = None
        if os.path.exists("session.json"):
            try:
                with open("session.json", encoding="utf-8") as f:
                    data = json.load(f)
                    # Support dua format: {"active_user": ...} atau {"username": ...}
                    active_user = data.get("active_user") or data.get("username")
            except Exception:
                pass

        if active_user:
            self.username = active_user
            self.show_page("dashboard")
        else:
            self.show_page("login")

    # ────────────────────────────────────────────── data
    def _load_local_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, encoding="utf-8") as f:
                    self.movie_list = json.load(f)
            except Exception:
                self.movie_list = []
        else:
            self.movie_list = []

        if not self.movie_list:
            t = threading.Thread(target=self._initialize_data, daemon=True)
            t.start()

    def _initialize_data(self):
        try:
            from scraper import MovieScraper
            scraper = MovieScraper()
            hasil = scraper.scrape_top_movies()
            if hasil:
                self.movie_list = hasil
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(self.movie_list, f, indent=4)
                print("✅ Database Ready!")
            scraper.close()
        except Exception as e:
            print(f"Scraper error: {e}")

    # ────────────────────────────────────────────── navigation
    def show_page(self, page_name: str, data=None):
        if self._welcome:
            self._welcome.cleanup()
            self._welcome = None

        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        widget = self._build_page(page_name, data)
        if widget:
            self.stack.addWidget(widget)
            self.stack.setCurrentWidget(widget)

    def _build_page(self, page_name: str, data=None) -> QWidget:
        # ── Dashboard
        if page_name == "dashboard":
            try:
                from dashboardCinephile import DashboardPage
                return DashboardPage(self, self)
            except Exception as e:
                print(f"[dashboard] Error: {e}")

        # ── Login
        elif page_name == "login":
            try:
                from loginPage import LoginPage
                return LoginPage(self, self)
            except Exception as e:
                print(f"[login] Error: {e}")

        # ── Movie Table
        elif page_name == "movietable":
            try:
                from movieTable import MovietablePage
                return MovietablePage(self, self)
            except Exception as e:
                print(f"[movietable] Error: {e}")

        # ── Watchlist
        elif page_name == "watchlist":
            try:
                from watchlist import WatchlistPage
                return WatchlistPage(self, self)
            except Exception as e:
                print(f"[watchlist] Error: {e}")

        # ── Genre Analyze
        elif page_name == "genreanalyze":
            try:
                from genreAnalyze import GenreAnalyzePage
                return GenreAnalyzePage(self, self)
            except Exception as e:
                print(f"[genreanalyze] Error: {e}")

        # ── Movie Detail
        elif page_name == "moviedetail":
            try:
                from movieDetail import MovieDetailPage
                return MovieDetailPage(self, self, data)
            except Exception as e:
                print(f"[moviedetail] Error: {e}")

        # ── Profile
        elif page_name == "profile":
            try:
                from profilePage import ProfilePage
                return ProfilePage(self, self)
            except Exception as e:
                print(f"[profile] Error: {e}")

        # ── Fallback placeholder
        placeholder = QWidget()
        placeholder.setStyleSheet("background:#0D0D0D;")
        lbl = QLabel(f"Page: {page_name}\n(Belum di-port ke PyQt6)", placeholder)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#FFFFFF; font-size:20px;")
        lbl.resize(self.width(), self.height())
        return placeholder

    # ────────────────────────────────────────────── welcome transition
    def show_welcome_transition(self, username: str):
        self.username = username
        self.stack.hide()

        welcome = WelcomeScreen(self.centralWidget(), self, username)
        welcome.setGeometry(self.centralWidget().rect())
        welcome.show()
        welcome.exit_requested.connect(self._welcome_exit)
        self._welcome = welcome

        self._fade_window(0.0, 1.0, duration_ms=250)

    def _welcome_exit(self):
        if self._welcome:
            self._welcome.cleanup()
            self._welcome.hide()
            self._welcome = None

        self.stack.show()
        self.show_page("dashboard")
        self._fade_window(0.0, 1.0, duration_ms=350)

    def _fade_window(self, from_alpha: float, to_alpha: float, duration_ms: int = 250):
        effect = QGraphicsOpacityEffect(self.centralWidget())
        self.centralWidget().setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(from_alpha)
        anim.setEndValue(to_alpha)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.centralWidget().setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ────────────────────────────────────────────── utilities
    def show_toast(self, message: str, target: str | None = None):
        print(f"Toast: {message}")
        if target:
            self.show_page(target)

    def handle_local_search(self, query: str):
        if not query:
            return
        self.search_query_pending = query.lower().strip()
        self.show_page("movietable")

    def logout_user(self):
        if os.path.exists("session.json"):
            try:
                os.remove("session.json")
            except Exception:
                pass
        self.username = "guest"
        self.show_page("login")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._welcome and self._welcome.isVisible():
            self._welcome.setGeometry(self.centralWidget().rect())

    def closeEvent(self, event):
        if self._welcome:
            self._welcome.cleanup()
        super().closeEvent(event)


# ══════════════════════════════════════════════════════════════ ENTRY POINT
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Cinephile")

    window = MainApp()
    window.show()
    sys.exit(app.exec())
