import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFrame, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor, QPainterPath, QImage
from PyQt6.QtCore import Qt, QSize
from PIL import Image, ImageDraw
import io


# ==========================================
# 1. DATABASE & SESSION (JSON)
# ==========================================
class UserDB:
    def __init__(self, db_file="users.json", session_file="session.json"):
        self.db_file = db_file
        self.session_file = session_file
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_data(self):
        with open(self.db_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def register_user(self, full_name, username, email, password):
        data = self._load_data()
        if username in data:
            return False, "Username sudah terdaftar!"
        data[username] = {"full_name": full_name, "email": email, "password": password}
        self._save_data(data)
        return True, "Akun berhasil dibuat!"

    def login_user(self, username, password):
        data = self._load_data()
        if username in data and data[username]["password"] == password:
            return True, "Login Berhasil!"
        return False, "Username atau Password salah!"

    def reset_password(self, username, new_password):
        data = self._load_data()
        if username not in data:
            return False, "Username tidak ditemukan!"
        data[username]["password"] = new_password
        self._save_data(data)
        return True, "Password berhasil diubah!"

    def save_session(self, username):
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump({"active_user": username, "username": username}, f)

    def get_session(self):
        if os.path.exists(self.session_file):
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_user")
        return None

    def clear_session(self):
        if os.path.exists(self.session_file):
            os.remove(self.session_file)

    def get_user_info(self, username):
        data = self._load_data()
        return data.get(username)

    def update_avatar_path(self, username, path):
        data = self._load_data()
        if username in data:
            data[username]["avatar_path"] = path
            self._save_data(data)

    def update_profile_info(self, username, full_name, email, bio, gender, dob):
        data = self._load_data()
        if username not in data:
            return False, "User tidak ditemukan!"
        data[username].update({"full_name": full_name, "email": email,
                               "bio": bio, "gender": gender, "dob": dob})
        self._save_data(data)
        return True, "Profil berhasil disimpan!"

    def change_password_secure(self, username, old_password, new_password):
        data = self._load_data()
        if username not in data:
            return False, "User tidak ditemukan!"
        if data[username]["password"] != old_password:
            return False, "Password lama salah!"
        data[username]["password"] = new_password
        self._save_data(data)
        return True, "Password berhasil diubah!"

    def delete_user(self, username):
        data = self._load_data()
        if username in data:
            del data[username]
            self._save_data(data)
            return True
        return False


# ── Helper: styled input ──────────────────────────────────────────────────────
def make_input(placeholder, echo_mode=QLineEdit.EchoMode.Normal, width=320):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setEchoMode(echo_mode)
    e.setFixedWidth(width)
    e.setFixedHeight(45)
    e.setStyleSheet("""
        QLineEdit {
            background: #2A2A2A;
            border: 1px solid #444;
            border-radius: 10px;
            color: white;
            font-size: 14px;
            padding: 0 14px;
        }
        QLineEdit:focus { border-color: #E53935; }
    """)
    return e


def make_button(text, primary=True, width=320):
    btn = QPushButton(text)
    btn.setFixedSize(width, 45)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        btn.setStyleSheet("""
            QPushButton {
                background: #631d2a;
                color: white;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #4a151f; }
        """)
    else:
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #AAAAAA;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover { color: white; }
        """)
    return btn


# ==========================================
# 2. AUTH PAGES
# ==========================================
class AuthPages(QWidget):
    def __init__(self, parent_widget, app):
        super().__init__(parent_widget)
        self.app = app
        self.db = UserDB()
        self.setStyleSheet("background: #1A1A1A;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_logo(self):
        logo_path = "Cinephile.png"
        lbl = QLabel()
        lbl.setFixedSize(130, 130)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert("RGBA")
                w, h = img.size
                m = min(w, h)
                img = img.crop(((w-m)//2, (h-m)//2, (w+m)//2, (h+m)//2))
                img = img.resize((120, 120), Image.LANCZOS)
                mask = Image.new("L", img.size, 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 120, 120), fill=255)
                img.putalpha(mask)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                qimg = QImage.fromData(buf.getvalue())
                lbl.setPixmap(QPixmap.fromImage(qimg).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except:
                lbl.setText("🎬")
                lbl.setFont(QFont("Arial", 40))
        else:
            lbl.setText("🎬")
            lbl.setFont(QFont("Arial", 40))
        return lbl

    def _center_widget(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        return w

    # ── LOGIN ──────────────────────────────────────────────────────────────
    def render_login(self):
        self._clear()
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(center)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(12)

        vl.addWidget(self._make_logo(), alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Log In Cinephile.")
        title.setFont(QFont("Inter", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(title)

        self.login_user_entry = make_input("Username")
        self.login_pass_entry = make_input("Password", QLineEdit.EchoMode.Password)
        vl.addWidget(self.login_user_entry, alignment=Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self.login_pass_entry, alignment=Qt.AlignmentFlag.AlignCenter)

        self.remember_cb = QCheckBox("Remember Me")
        self.remember_cb.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        vl.addWidget(self.remember_cb, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_login = make_button("Log in")
        btn_login.clicked.connect(self._handle_login)
        vl.addWidget(btn_login, alignment=Qt.AlignmentFlag.AlignCenter)

        reg_btn = make_button("Don't have an account? Create one", primary=False)
        reg_btn.clicked.connect(lambda: self.app.show_page("register"))
        vl.addWidget(reg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        forgot_btn = make_button("Forgot your password?", primary=False)
        forgot_btn.clicked.connect(lambda: self.app.show_page("forgot_password"))
        vl.addWidget(forgot_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer = QVBoxLayout()
        outer.addStretch()
        outer.addWidget(center, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()

        container = QWidget()
        container.setLayout(outer)
        container.setStyleSheet("background: #1A1A1A;")
        self._layout.addWidget(container)

    def _handle_login(self):
        username = self.login_user_entry.text().strip()
        password = self.login_pass_entry.text().strip()
        if not username or not password:
            self.app.show_toast("Harap isi semua kolom!")
            return
        success, message = self.db.login_user(username, password)
        if success:
            self.db.save_session(username)
            self.app.show_toast(message, target="dashboard")
        else:
            self.app.show_toast(message)

    # ── REGISTER ──────────────────────────────────────────────────────────
    def render_register(self):
        self._clear()
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(center)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(10)

        vl.addWidget(self._make_logo(), alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Sign Up Cinephile.")
        title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(title)

        self.reg_entries = {}
        for field in ["Full Name", "Username", "Email", "Password"]:
            e = make_input(field, QLineEdit.EchoMode.Password if field == "Password" else QLineEdit.EchoMode.Normal)
            self.reg_entries[field] = e
            vl.addWidget(e, alignment=Qt.AlignmentFlag.AlignCenter)

        btn = make_button("Create Account")
        btn.clicked.connect(self._handle_register)
        vl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        back = make_button("Already have an account? Log In", primary=False)
        back.clicked.connect(lambda: self.app.show_page("login"))
        vl.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

        outer = QVBoxLayout()
        outer.addStretch()
        outer.addWidget(center, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()
        container = QWidget()
        container.setLayout(outer)
        container.setStyleSheet("background: #1A1A1A;")
        self._layout.addWidget(container)

    def _handle_register(self):
        fn = self.reg_entries["Full Name"].text().strip()
        un = self.reg_entries["Username"].text().strip()
        em = self.reg_entries["Email"].text().strip()
        pw = self.reg_entries["Password"].text().strip()
        if not all([fn, un, em, pw]):
            self.app.show_toast("Harap isi semua kolom!")
            return
        success, message = self.db.register_user(fn, un, em, pw)
        if success:
            self.app.show_toast(message, target="login")
        else:
            self.app.show_toast(message)

    # ── FORGOT PASSWORD ────────────────────────────────────────────────────
    def render_forgot_password(self):
        self._clear()
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(center)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(10)

        vl.addWidget(self._make_logo(), alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Forgot Password?")
        title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(title)

        self.fg_user  = make_input("Enter username")
        self.fg_pass1 = make_input("Enter new password", QLineEdit.EchoMode.Password)
        self.fg_pass2 = make_input("Confirm new password", QLineEdit.EchoMode.Password)
        for w in [self.fg_user, self.fg_pass1, self.fg_pass2]:
            vl.addWidget(w, alignment=Qt.AlignmentFlag.AlignCenter)

        btn = make_button("Reset Password")
        btn.clicked.connect(self._handle_forgot_password)
        vl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        back = make_button("Back to Login", primary=False)
        back.clicked.connect(lambda: self.app.show_page("login"))
        vl.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

        outer = QVBoxLayout()
        outer.addStretch()
        outer.addWidget(center, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()
        container = QWidget()
        container.setLayout(outer)
        container.setStyleSheet("background: #1A1A1A;")
        self._layout.addWidget(container)

    def _handle_forgot_password(self):
        un = self.fg_user.text().strip()
        p1 = self.fg_pass1.text().strip()
        p2 = self.fg_pass2.text().strip()
        if not all([un, p1, p2]):
            self.app.show_toast("Harap isi semua kolom!")
            return
        if p1 != p2:
            self.app.show_toast("Password tidak sama!")
            return
        success, message = self.db.reset_password(un, p1)
        if success:
            self.app.show_toast(message, target="login")
        else:
            self.app.show_toast(message)
