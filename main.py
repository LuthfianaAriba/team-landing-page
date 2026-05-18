from __future__ import annotations  # FIX: support 'X | Y' type hints di Python < 3.10

import json
import os
import random
import sys
import threading

from PyQt6.QtCore import (
    QEasingCurve, QObject, QPropertyAnimation, QRect,
    QThread, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QCursor, QFont, QImage, QPainter,
    QPainterPath, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QGraphicsOpacityEffect, QLabel,
    QMainWindow, QStackedWidget, QWidget,
)

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── poster grid constants ─────────────────────────────────────────────────
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

_POSTER_CACHE: list[QPixmap] = []


# ══════════════════════════════════ background poster worker ══════════════
class _PosterWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, movie_list: list) -> None:
        super().__init__()
        self.movie_list = movie_list

    def run(self) -> None:
        global _POSTER_CACHE
        if not PIL_AVAILABLE:
            self.finished.emit([])
            return

        pool = [
            m for m in self.movie_list
            if m.get("poster_local") and os.path.exists(m["poster_local"])
        ]
        if not pool:
            self.finished.emit([])
            return

        random.shuffle(pool)
        while len(pool) < _N:
            pool = pool * 2
        pool = pool[:_N]

        pixmaps: list[QPixmap] = []
        for m in pool:
            try:
                img = Image.open(m["poster_local"]).convert("RGB")
                img = img.resize((_POSTER_W, _POSTER_H), Image.LANCZOS)
                img = img.filter(ImageFilter.GaussianBlur(1.5))
                img = ImageEnhance.Brightness(img).enhance(0.25)
                data = img.tobytes("raw", "RGB")
                qi = QImage(data, _POSTER_W, _POSTER_H, QImage.Format.Format_RGB888)
                pixmaps.append(QPixmap.fromImage(qi))
            except Exception:
                px = QPixmap(_POSTER_W, _POSTER_H)
                px.fill(QColor(20, 20, 20))
                pixmaps.append(px)

        _POSTER_CACHE = pixmaps
        self.finished.emit(pixmaps)


# ══════════════════════════════════════════════════════ WELCOME SCREEN ════
class WelcomeScreen(QWidget):
    go_to_dashboard = pyqtSignal()

    _STRIP_W = 44

    def __init__(self, parent: QWidget, app: object, username: str) -> None:
        super().__init__(parent)
        self.app      = app
        self.username = username
        self.setMouseTracking(True)

        self._mouse_x  = 0.0
        self._mouse_y  = 0.0
        self._smooth_x = 0.0
        self._smooth_y = 0.0

        self._posters: list[dict] = []

        self._btn_rect    = QRect(0, 0, 0, 0)
        self._btn_hovered = False
        self._btn_clicked = False

        self._fade_alpha = 0
        self._fade_step  = 0
        self._fading_out = False

        self._parallax_timer = QTimer(self)
        self._parallax_timer.setInterval(16)
        self._parallax_timer.timeout.connect(self._tick_parallax)
        self._parallax_timer.start()

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(18)
        self._fade_timer.timeout.connect(self._tick_fadeout)

        self._load_posters()

    # ── poster loading ────────────────────────────────────────────────────
    def _load_posters(self) -> None:
        global _POSTER_CACHE
        if _POSTER_CACHE:
            QTimer.singleShot(50, lambda: self._on_posters_ready(_POSTER_CACHE[:]))
        else:
            self._thread = QThread()
            self._worker = _PosterWorker(getattr(self.app, "movie_list", []))
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self._on_posters_ready)
            self._worker.finished.connect(self._thread.quit)
            self._thread.start()

    def _on_posters_ready(self, pixmaps: list) -> None:
        if not pixmaps:
            return
        w = self.width()  or 1100
        h = self.height() or 850
        self._posters.clear()
        for i, px in enumerate(pixmaps[:_N]):
            rx, ry, depth = _GRID[i]
            jx = random.randint(-4, 4)
            jy = random.randint(-4, 4)
            self._posters.append({
                "pixmap": px,
                "base_x": rx * w + jx,
                "base_y": ry * h + jy,
                "rx": rx, "ry": ry,
                "jx": jx, "jy": jy,
                "depth": depth,
            })
        self.update()

    # ── layout ────────────────────────────────────────────────────────────
    def _recalc_layout(self, w: int, h: int) -> None:
        bw, bh = 230, 48
        bx = w // 2 - bw // 2
        by = int(h * 0.64) - bh // 2
        self._btn_rect = QRect(bx, by, bw, bh)
        for p in self._posters:
            p["base_x"] = p["rx"] * w + p["jx"]
            p["base_y"] = p["ry"] * h + p["jy"]

    def resizeEvent(self, event: object) -> None:  # type: ignore[override]
        super().resizeEvent(event)  # type: ignore[arg-type]
        self._smooth_x = self.width()  / 2
        self._smooth_y = self.height() / 2
        self._recalc_layout(self.width(), self.height())

    # ── mouse ─────────────────────────────────────────────────────────────
    def mouseMoveEvent(self, event: object) -> None:  # type: ignore[override]
        pos = event.position()  # type: ignore[attr-defined]
        self._mouse_x = float(pos.x())
        self._mouse_y = float(pos.y())
        hov = self._btn_rect.contains(int(self._mouse_x), int(self._mouse_y))
        if hov != self._btn_hovered:
            self._btn_hovered = hov
            self.setCursor(QCursor(
                Qt.CursorShape.PointingHandCursor if hov
                else Qt.CursorShape.ArrowCursor
            ))
            self.update()

    def mousePressEvent(self, event: object) -> None:  # type: ignore[override]
        btn = event.button()  # type: ignore[attr-defined]
        if btn == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()  # type: ignore[attr-defined]
            if self._btn_rect.contains(pos):
                self._go()

    # ── parallax ──────────────────────────────────────────────────────────
    def _tick_parallax(self) -> None:
        ease = 0.07
        self._smooth_x += (self._mouse_x - self._smooth_x) * ease
        self._smooth_y += (self._mouse_y - self._smooth_y) * ease
        self.update()

    # ── fade-out ──────────────────────────────────────────────────────────
    def _go(self) -> None:
        if self._btn_clicked or self._fading_out:
            return
        self._btn_clicked = True
        self._fading_out  = True
        self._parallax_timer.stop()
        self._fade_step  = 0
        self._fade_alpha = 0
        self._fade_timer.start()

    def _tick_fadeout(self) -> None:
        total = 20
        self._fade_step += 1
        progress = self._fade_step / total

        if   progress < 0.15: self._fade_alpha = 0
        elif progress < 0.30: self._fade_alpha = 40
        elif progress < 0.45: self._fade_alpha = 80
        elif progress < 0.60: self._fade_alpha = 140
        elif progress < 0.75: self._fade_alpha = 200
        else:                  self._fade_alpha = 255

        self.update()

        if self._fade_step >= total:
            self._fade_timer.stop()
            QTimer.singleShot(60, self.go_to_dashboard.emit)

    # ── paint ─────────────────────────────────────────────────────────────
    def paintEvent(self, event: object) -> None:  # type: ignore[override]
        pr = QPainter(self)
        pr.setRenderHint(QPainter.RenderHint.Antialiasing)
        pr.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        pr.fillRect(self.rect(), QColor("#0D0D0D"))

        # film-strip
        for sx in (0, w - self._STRIP_W):
            pr.fillRect(sx, 0, self._STRIP_W, h, QColor("#1C1C1C"))
            for i in range(120):
                pr.fillRect(sx + 15, 10 + i * 36, 14, 9, QColor("#0D0D0D"))

        # parallax posters
        if self._posters:
            ox = max(-1.0, min(1.0, (self._smooth_x - cx) / max(cx, 1)))
            oy = max(-1.0, min(1.0, (self._smooth_y - cy) / max(cy, 1)))
            for item in self._posters:
                px = int(item["base_x"] + ox * 30 * item["depth"])
                py = int(item["base_y"] + oy * 20 * item["depth"])
                pr.drawPixmap(px, py, item["pixmap"])

        # tag line
        pr.setPen(QColor("#666666"))
        f = QFont("Trebuchet MS", 11); f.setBold(True)
        pr.setFont(f)
        pr.drawText(
            QRect(0, int(h * 0.33) - 20, w, 40),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "✦  CINEPHILE  ·  YOUR CINEMA UNIVERSE",
        )

        # welcome back
        pr.setPen(QColor("#FFFFFF"))
        f = QFont("Georgia", 42); f.setBold(True)
        pr.setFont(f)
        pr.drawText(
            QRect(0, int(h * 0.40) - 35, w, 70),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Welcome back,",
        )

        # username
        pr.setPen(QColor("#E8A020"))
        f = QFont("Georgia", 50); f.setBold(True)
        pr.setFont(f)
        pr.drawText(
            QRect(0, int(h * 0.49) - 40, w, 80),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            self.username,
        )

        # stats
        stats = self._get_stats()
        pr.setPen(QColor("#BBBBBB"))
        pr.setFont(QFont("Trebuchet MS", 13))
        pr.drawText(
            QRect(0, int(h * 0.56) - 20, w, 40),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            f"{stats['films']} films  ·  "
            f"{stats['watchlist']} watchlists  ·  "
            f"{stats['rating']} avg rating",
        )

        # button
        btn_color = QColor("#C62828") if self._btn_hovered else QColor("#b03535")
        path = QPainterPath()
        path.addRoundedRect(
            float(self._btn_rect.x()),    float(self._btn_rect.y()),
            float(self._btn_rect.width()), float(self._btn_rect.height()),
            24.0, 24.0,
        )
        pr.fillPath(path, btn_color)
        pr.setPen(QColor("#FFFFFF"))
        f = QFont("Trebuchet MS", 14); f.setBold(True)
        pr.setFont(f)
        pr.drawText(
            self._btn_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "▶   Lanjutkan menonton",
        )

        # fade overlay
        if self._fade_alpha > 0:
            pr.fillRect(self.rect(), QColor(0, 0, 0, min(255, self._fade_alpha)))

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

    def cleanup(self) -> None:
        self._parallax_timer.stop()
        self._fade_timer.stop()


# ═══════════════════════════════════════════════════════════════ MAIN APP ═
class MainApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cinephile App")
        self.resize(1100, 850)
        self.setStyleSheet("background-color: #1A1A1A;")

        self.db_path  = "data_film.json"
        self.username = "guest"
        self.is_admin = False
        self.movie_list: list = []
        self.search_query_pending: str = ""
        self._welcome: WelcomeScreen | None = None
        self._active_anim: QPropertyAnimation | None = None
        self._img_cache: dict = {}

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._load_local_data()

        active_user: str | None = None
        if os.path.exists("session.json"):
            try:
                with open("session.json", encoding="utf-8") as f:
                    active_user = json.load(f).get("active_user")
            except Exception:
                pass

        if active_user:
            self.username = active_user
            self.show_page("dashboard")
        else:
            self.show_page("login")

    # ── data ──────────────────────────────────────────────────────────────
    def _load_local_data(self) -> None:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, encoding="utf-8") as f:
                    self.movie_list = json.load(f)
            except Exception:
                self.movie_list = []
        else:
            self.movie_list = []

        if not self.movie_list:
            threading.Thread(target=self._initialize_data, daemon=True).start()

    def _initialize_data(self) -> None:
        try:
            from scraper import MovieScraper  # type: ignore[import]
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

    # ── navigasi ──────────────────────────────────────────────────────────
    def show_page(self, page_name: str, data: dict | None = None) -> None:
        if self._welcome:
            self._welcome.cleanup()
            self._welcome = None

        while self.stack.count():
            old = self.stack.widget(0)
            self.stack.removeWidget(old)
            old.deleteLater()

        widget = self._make_page(page_name, data)
        if widget:
            self.stack.addWidget(widget)
            self.stack.setCurrentWidget(widget)
            widget.show()

    def _make_page(self, page_name: str, data: dict | None = None) -> QWidget | None:
        if page_name == "dashboard":
            from dashboardCinephile import DashboardPage  # type: ignore[import]
            return DashboardPage(self.stack, self)

        elif page_name == "login":
            # from loginPage_qt import LoginPage
            # return LoginPage(self.stack, self)
            return _placeholder("Login Page\n(port loginPage.py ke PyQt6)")

        elif page_name == "register":
            return _placeholder("Register Page\n(port loginPage.py ke PyQt6)")

        elif page_name == "profile":
            # from profilePage_qt import ProfilePage
            # return ProfilePage(self.stack, self)
            return _placeholder("Profile Page\n(port profilePage.py ke PyQt6)")

        elif page_name == "movietable":
            # from movieTable_qt import MovietablePage
            # return MovietablePage(self.stack, self)
            return _placeholder("Movie Table\n(port movieTable.py ke PyQt6)")

        elif page_name == "genreanalyze":
            # from genreAnalyze_qt import GenreAnalyzePage
            # return GenreAnalyzePage(self.stack, self)
            return _placeholder("Genre Analyze\n(port genreAnalyze.py ke PyQt6)")

        elif page_name == "moviedetail":
            # from movieDetail_qt import MovieDetailPage
            # return MovieDetailPage(self.stack, self, movie_data=data)
            title = data.get("title", "") if data else ""
            return _placeholder(f"Movie Detail: {title}\n(port movieDetail.py ke PyQt6)")

        elif page_name == "watchlist":
            # from watchlist_qt import WatchlistPage
            # return WatchlistPage(self.stack, self)
            return _placeholder("Watchlist\n(port watchlist.py ke PyQt6)")

        return None

    # ── welcome transition ────────────────────────────────────────────────
    def show_welcome_transition(self, username: str) -> None:
        self.username = username
        self.stack.hide()

        welcome = WelcomeScreen(self.centralWidget(), self, username)
        welcome.setGeometry(self.centralWidget().rect())
        welcome.show()
        welcome.go_to_dashboard.connect(self._do_welcome_to_dashboard)
        self._welcome = welcome

        self._animate_opacity(0.0, 1.0, duration_ms=240,
                              easing=QEasingCurve.Type.InOutCubic)

    def _do_welcome_to_dashboard(self) -> None:
        if self._welcome:
            self._welcome.cleanup()
            self._welcome.hide()
            self._welcome.deleteLater()
            self._welcome = None

        self.stack.show()
        self.show_page("dashboard")
        self._animate_opacity(0.0, 1.0, duration_ms=308,
                              easing=QEasingCurve.Type.OutCubic)

    def _animate_opacity(
        self,
        start: float,
        end: float,
        duration_ms: int,
        easing: QEasingCurve.Type,
    ) -> None:
        effect = QGraphicsOpacityEffect(self.centralWidget())
        self.centralWidget().setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(easing)
        anim.finished.connect(
            lambda: self.centralWidget().setGraphicsEffect(None)
        )
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._active_anim = anim

    # ── utilities ─────────────────────────────────────────────────────────
    def show_toast(self, message: str, target: str | None = None) -> None:
        print(f"Toast: {message}")
        if target:
            self.show_page(target)

    def handle_local_search(self, query: str) -> None:
        if not query:
            return
        self.search_query_pending = query.lower().strip()
        self.show_page("movietable")

    def logout_user(self) -> None:
        if os.path.exists("session.json"):
            try:
                os.remove("session.json")
            except Exception:
                pass
        self.username = "guest"
        self.show_page("login")

    # ── resize / close ────────────────────────────────────────────────────
    def resizeEvent(self, event: object) -> None:  # type: ignore[override]
        super().resizeEvent(event)  # type: ignore[arg-type]
        if self._welcome and self._welcome.isVisible():
            self._welcome.setGeometry(self.centralWidget().rect())

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        if self._welcome:
            self._welcome.cleanup()
        super().closeEvent(event)  # type: ignore[arg-type]


# ── helper ────────────────────────────────────────────────────────────────
def _placeholder(msg: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background:#0D0D0D;")
    lbl = QLabel(msg, w)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("color:#AAAAAA; font-size:18px;")
    lbl.setGeometry(0, 0, 1100, 850)
    return w


# ═══════════════════════════════════════════════════════════════ ENTRY ════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Cinephile")
    window = MainApp()
    window.show()
    sys.exit(app.exec())
