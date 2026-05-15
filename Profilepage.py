import json
import os
from PyQt6 import QtCore, QtGui, QtWidgets


class ProfileWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, app=None, **kwargs):
        super().__init__(parent)
        self.app = app

        # ── Ambil username dari session ──────────────────────────────────────
        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json", "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", "Guest")
        except Exception:
            pass

        self.setStyleSheet("background: transparent;")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Avatar bulat
        initial = self.username[0].upper() if self.username else "G"
        self.avatar = QtWidgets.QLabel(initial)
        self.avatar.setFixedSize(35, 35)
        self.avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("""
            QLabel {
                background-color: #E50914;
                color: white;
                border-radius: 17px;
                font-family: Helvetica;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.avatar)

        # Nama user
        self.user_info = QtWidgets.QLabel(self.username)
        self.user_info.setStyleSheet("""
            QLabel {
                color: white;
                font-family: Helvetica;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.user_info)

        # Tombol logout
        self.logout_btn = QtWidgets.QPushButton("Logout")
        self.logout_btn.setFixedSize(70, 28)
        self.logout_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border-radius: 4px;
                font-family: Helvetica;
                font-size: 11px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #E50914; }
        """)
        self.logout_btn.clicked.connect(self._confirm_logout)
        layout.addWidget(self.logout_btn)

    def _confirm_logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Konfirmasi Logout",
            f"Halo {self.username}, apakah kamu yakin ingin keluar dari aplikasi?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            print(f"User {self.username} logged out.")
            if self.app and hasattr(self.app, "logout"):
                self.app.logout()