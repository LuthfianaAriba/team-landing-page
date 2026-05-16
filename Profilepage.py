import os
import json
import re
import shutil
import io
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QComboBox, QDialog, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageDraw, ImageOps
from loginPage import UserDB

BG_MAIN  = "#1A1A1A"
BG_NAV   = "#111111"
BG_TAB   = "#2E2E2E"
ACCENT   = "#E53935"
TEXT_GRAY = "#AAAAAA"


def pil_to_qpixmap(pil_img, size=None):
    if size:
        try:
            pil_img = ImageOps.fit(pil_img, size, Image.LANCZOS)
        except:
            pil_img = pil_img.resize(size, Image.LANCZOS)
    pil_img = pil_img.convert("RGBA")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))


def make_circular_pixmap(path, size=120, border=4):
    """Buat pixmap bulat dengan border putih."""
    try:
        img = Image.open(path).convert("RGBA")
        img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))

        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)

        total = size + border * 2
        final = Image.new("RGBA", (total, total), (0, 0, 0, 0))
        ImageDraw.Draw(final).ellipse((0, 0, total, total), fill="white")
        final.paste(img, (border, border), img)

        return pil_to_qpixmap(final)
    except Exception as e:
        print(f"Avatar error: {e}")
        return None


def make_input(placeholder, echo=False, width=400):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setFixedHeight(45)
    if width: e.setFixedWidth(width)
    if echo: e.setEchoMode(QLineEdit.EchoMode.Password)
    e.setStyleSheet("""
        QLineEdit { background: #1e1e1e; border: 1px solid #333; border-radius: 8px;
                    color: white; font-size: 14px; padding: 0 14px; }
        QLineEdit:focus { border-color: #E53935; }
    """)
    return e


def make_btn(text, primary=True, width=400, height=45):
    btn = QPushButton(text)
    btn.setFixedSize(width, height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        btn.setStyleSheet("""
            QPushButton { background: #E53935; color: white; border-radius: 10px;
                          font-size: 14px; font-weight: bold; border: none; }
            QPushButton:hover { background: #c0392b; }
        """)
    else:
        btn.setStyleSheet("""
            QPushButton { background: transparent; color: #AAAAAA; border: 1px solid #333;
                          border-radius: 10px; font-size: 13px; }
            QPushButton:hover { color: white; border-color: #555; }
        """)
    return btn


class ProfilePage(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = UserDB()
        self.setStyleSheet(f"background: {BG_MAIN};")

        self.username = "Guest"
        try:
            if os.path.exists("session.json"):
                with open("session.json") as f:
                    s = json.load(f)
                    self.username = s.get("active_user", s.get("username", "Guest"))
        except: pass

        self.user_data = self.db.get_user_info(self.username) or {}
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Back button
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background: {BG_MAIN};")
        top_bar.setFixedHeight(60)
        tbl = QHBoxLayout(top_bar)
        tbl.setContentsMargins(30, 10, 30, 10)
        back_btn = QPushButton("◀ Back to Dashboard")
        back_btn.setFixedSize(180, 36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{ background: {BG_TAB}; color: white; border-radius: 18px;
                          font-size: 12px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        back_btn.clicked.connect(lambda: self.app.show_page("dashboard"))
        tbl.addWidget(back_btn)
        tbl.addStretch()
        main_layout.addWidget(top_bar)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(0, 20, 0, 40)

        # Card container
        card = QWidget()
        card.setFixedWidth(620)
        card.setStyleSheet(f"background: {BG_NAV}; border-radius: 20px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(10)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Avatar
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(136, 136)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_avatar()
        card_layout.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        change_photo_btn = QPushButton("📷 Change Photo")
        change_photo_btn.setFixedSize(140, 32)
        change_photo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_photo_btn.setStyleSheet("""
            QPushButton { background: #333; color: white; border-radius: 16px;
                          font-size: 11px; border: none; }
            QPushButton:hover { background: #444; }
        """)
        change_photo_btn.clicked.connect(self._change_avatar)
        card_layout.addWidget(change_photo_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        username_lbl = QLabel(f"@{self.username}")
        username_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        username_lbl.setStyleSheet(f"color: {TEXT_GRAY}; background: transparent;")
        username_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(username_lbl)

        card_layout.addSpacing(10)

        # Form fields
        self.fn_entry = self._add_field(card_layout, "Full Name", self.user_data.get("full_name", ""))
        self.em_entry = self._add_field(card_layout, "Email Address", self.user_data.get("email", ""))
        self.bio_entry = self._add_field(card_layout, "Bio / Quote", self.user_data.get("bio", ""))

        # Gender
        g_lbl = QLabel("Gender")
        g_lbl.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 11px; background: transparent;")
        card_layout.addWidget(g_lbl)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        self.gender_combo.setCurrentText(self.user_data.get("gender", "Male"))
        self.gender_combo.setFixedHeight(40)
        self.gender_combo.setStyleSheet("""
            QComboBox { background: #1e1e1e; border: 1px solid #333; border-radius: 8px;
                        color: white; font-size: 14px; padding: 0 14px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e1e1e; color: white; }
        """)
        card_layout.addWidget(self.gender_combo)

        # DOB
        self.dob_entry = self._add_field(card_layout, "Date of Birth (DD-MM-YYYY)", self.user_data.get("dob", ""))

        card_layout.addSpacing(10)

        # Security section
        sec_frame = QWidget()
        sec_frame.setStyleSheet("background: #1a1a1a; border-radius: 10px;")
        sec_layout = QVBoxLayout(sec_frame)
        sec_layout.setContentsMargins(15, 15, 15, 15)

        sec_title = QLabel("Account Security")
        sec_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        sec_title.setStyleSheet("color: white; background: transparent;")
        sec_layout.addWidget(sec_title)

        sec_sub = QLabel("Password is set and secured.")
        sec_sub.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 12px; background: transparent;")
        sec_layout.addWidget(sec_sub)

        pw_btn = QPushButton("🔒 Change Password")
        pw_btn.setFixedSize(180, 36)
        pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pw_btn.setStyleSheet("""
            QPushButton { background: #333; color: white; border-radius: 8px;
                          font-size: 12px; font-weight: bold; border: none; }
            QPushButton:hover { background: #444; }
        """)
        pw_btn.clicked.connect(self._open_change_password)
        sec_layout.addWidget(pw_btn, alignment=Qt.AlignmentFlag.AlignRight)
        card_layout.addWidget(sec_frame)

        card_layout.addSpacing(10)

        # Action buttons
        save_btn = make_btn("Save Profile Changes", primary=True)
        save_btn.clicked.connect(self._save_profile)
        card_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        logout_btn = make_btn("Logout", primary=False)
        logout_btn.clicked.connect(self._logout)
        card_layout.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        del_btn = QPushButton("Delete Account")
        del_btn.setFixedSize(400, 36)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("background: transparent; color: #c0392b; border: none; font-size: 13px;")
        del_btn.clicked.connect(self._delete_account)
        card_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _add_field(self, layout, label, value=""):
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 11px; background: transparent;")
        layout.addWidget(lbl)
        entry = make_input("", width=0)
        entry.setText(value)
        entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(entry)
        return entry

    def _load_avatar(self):
        path = self.user_data.get("avatar_path", "")
        if path and os.path.exists(path):
            px = make_circular_pixmap(path, size=120, border=4)
            if px:
                self.avatar_lbl.setPixmap(px)
                self.avatar_lbl.setStyleSheet("background: transparent;")
                return
        # Fallback: inisial
        initial = self.username[0].upper() if self.username else "G"
        self.avatar_lbl.setText(initial)
        self.avatar_lbl.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.avatar_lbl.setStyleSheet(f"""
            background: {ACCENT}; color: white; border-radius: 68px;
        """)

    def _change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "",
                                               "Image Files (*.png *.jpg *.jpeg)")
        if not path:
            return
        if not os.path.exists("avatars"):
            os.makedirs("avatars")
        dest = os.path.join("avatars", f"{self.username}.jpg")
        try:
            img = Image.open(path).convert("RGB")
            img.save(dest, "JPEG")
            self.db.update_avatar_path(self.username, dest)
            self.user_data = self.db.get_user_info(self.username)
            self._load_avatar()
            QMessageBox.information(self, "Success", "Photo updated!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {e}")

    def _open_change_password(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Change Password")
        dlg.setFixedSize(460, 520)
        dlg.setStyleSheet("background: #1A1A1A; color: white;")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(10)

        title = QLabel("🔒 Security Update")
        title.setFont(QFont("Arial Black", 20))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel(f"Updating password for @{self.username}")
        sub.setStyleSheet(f"color: {TEXT_GRAY}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(10)

        old_entry = make_input("Current Password", echo=True, width=0)
        old_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(old_entry)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #333;")
        layout.addWidget(sep)

        new_entry = make_input("New Password", echo=True, width=0)
        new_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        conf_entry = make_input("Confirm New Password", echo=True, width=0)
        conf_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(new_entry)
        layout.addWidget(conf_entry)

        # Requirements
        req_frame = QWidget()
        req_frame.setStyleSheet("background: #141414; border-radius: 8px;")
        req_layout = QVBoxLayout(req_frame)
        req_layout.setContentsMargins(10, 10, 10, 10)

        req_title = QLabel("Password Requirements:")
        req_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        req_title.setStyleSheet("color: white; background: transparent;")
        req_layout.addWidget(req_title)

        crit_len   = QLabel("• Minimum 8 characters")
        crit_upper = QLabel("• At least 1 Uppercase letter (A-Z)")
        crit_num   = QLabel("• At least 1 Number (0-9)")
        for c in [crit_len, crit_upper, crit_num]:
            c.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 11px; background: transparent;")
            req_layout.addWidget(c)
        layout.addWidget(req_frame)

        submit_btn = QPushButton("Update Password")
        submit_btn.setFixedHeight(45)
        submit_btn.setEnabled(False)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton { background: #E53935; color: white; border-radius: 10px;
                          font-size: 14px; font-weight: bold; border: none; }
            QPushButton:disabled { background: #555; color: #888; }
            QPushButton:hover:!disabled { background: #c0392b; }
        """)
        layout.addWidget(submit_btn)

        is_valid = [False]

        def validate(text):
            pwd = new_entry.text()
            v_len   = len(pwd) >= 8
            v_upper = bool(re.search(r'[A-Z]', pwd))
            v_num   = bool(re.search(r'\d', pwd))
            OK = "#2ecc71"
            crit_len.setStyleSheet(f"color: {OK if v_len else TEXT_GRAY}; font-size: 11px; background: transparent;")
            crit_upper.setStyleSheet(f"color: {OK if v_upper else TEXT_GRAY}; font-size: 11px; background: transparent;")
            crit_num.setStyleSheet(f"color: {OK if v_num else TEXT_GRAY}; font-size: 11px; background: transparent;")
            is_valid[0] = all([v_len, v_upper, v_num])
            submit_btn.setEnabled(is_valid[0])

        new_entry.textChanged.connect(validate)

        def do_submit():
            if not is_valid[0]:
                return
            if new_entry.text() != conf_entry.text():
                QMessageBox.critical(dlg, "Error", "Password tidak cocok dengan konfirmasi.")
                return
            if old_entry.text() == new_entry.text():
                QMessageBox.warning(dlg, "Input", "Sandi baru tidak boleh sama dengan sandi lama.")
                return
            ok, msg = self.db.change_password_secure(self.username, old_entry.text(), new_entry.text())
            if ok:
                QMessageBox.information(dlg, "Success", msg)
                dlg.accept()
            else:
                QMessageBox.critical(dlg, "Error", msg)

        submit_btn.clicked.connect(do_submit)
        dlg.exec()

    def _save_profile(self):
        fn  = self.fn_entry.text().strip()
        em  = self.em_entry.text().strip()
        bio = self.bio_entry.text().strip()
        gen = self.gender_combo.currentText()
        dob = self.dob_entry.text().strip()

        if not fn or not em or not dob:
            QMessageBox.warning(self, "Input", "Full Name, Email, dan DOB wajib diisi.")
            return
        if not re.match(r'^\d{2}-\d{2}-\d{4}$', dob):
            QMessageBox.warning(self, "Input", "Format DOB salah. Gunakan DD-MM-YYYY (misal: 17-08-1945)")
            return

        ok, msg = self.db.update_profile_info(self.username, fn, em, bio, gen, dob)
        QMessageBox.information(self, "Profile", msg)
        self.user_data = self.db.get_user_info(self.username)

    def _logout(self):
        reply = QMessageBox.question(self, "Confirm", "Logout dari akun?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if os.path.exists("session.json"):
                os.remove("session.json")
            self.app.show_page("login")

    def _delete_account(self):
        reply = QMessageBox.question(self, "⚠️ DANGER",
                                     "Hapus akun secara permanen? Semua data watchlist & review akan hilang.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            path = self.user_data.get("avatar_path", "")
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass
            if self.db.delete_user(self.username):
                if os.path.exists("session.json"): os.remove("session.json")
                wl = f"watchlist_{self.username}.json"
                if os.path.exists(wl): os.remove(wl)
                self.app.show_page("login")
