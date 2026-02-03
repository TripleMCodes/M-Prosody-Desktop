from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt


class AuthChoiceDialog(QDialog):
    """
    Startup dialog. User chooses Offline or logs in/signs up.
    """
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("M-Prosody — Online Features")
        self.setModal(True)
        self.resize(420, 260)

        self.result_mode = None  # "offline" | "online"

        layout = QVBoxLayout(self)

        title = QLabel("Enable online features?")
        title.setAlignment(Qt.AlignHCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Online features include cloud sync and online endpoints.\n"
            "You can use Lyrical Lab offline without signing in."
        )
        subtitle.setAlignment(Qt.AlignHCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "Log in")
        self.tabs.addTab(self._build_signup_tab(), "Sign up")
        layout.addWidget(self.tabs)

        # bottom row: offline + close
        bottom = QHBoxLayout()
        self.offline_btn = QPushButton("Continue offline")
        self.offline_btn.clicked.connect(self._choose_offline)

        self.cancel_btn = QPushButton("Not now")
        self.cancel_btn.clicked.connect(self._choose_offline)

        bottom.addWidget(self.offline_btn)
        bottom.addStretch(1)
        bottom.addWidget(self.cancel_btn)

        layout.addLayout(bottom)

    def _choose_offline(self):
        self.result_mode = "offline"
        self.accept()

    def _choose_online(self):
        self.result_mode = "online"
        self.accept()

    def _build_login_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)

        l.addWidget(self.login_email)
        l.addWidget(self.login_password)

        btn_row = QHBoxLayout()
        login_btn = QPushButton("Log in")
        login_btn.clicked.connect(self._do_login)
        btn_row.addStretch(1)
        btn_row.addWidget(login_btn)
        l.addLayout(btn_row)

        return w

    def _build_signup_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        self.signup_email = QLineEdit()
        self.signup_email.setPlaceholderText("Email")
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Password")
        self.signup_password.setEchoMode(QLineEdit.Password)
        self.name =  QLineEdit()
        self.name.setPlaceholderText("Name")
        self.age = QLineEdit()
        self.age.setPlaceholderText('Age')

        l.addWidget(self.name)
        l.addWidget(self.age)
        l.addWidget(self.signup_email)
        l.addWidget(self.signup_password)

        btn_row = QHBoxLayout()
        signup_btn = QPushButton("Create account")
        signup_btn.clicked.connect(self._do_signup)
        btn_row.addStretch(1)
        btn_row.addWidget(signup_btn)
        l.addLayout(btn_row)

        return w

    def _do_login(self):
        email = self.login_email.text().strip()
        pw = self.login_password.text().strip()
        print(email)
        print(pw)
        if not email or not pw:
            QMessageBox.warning(self, "Missing info", "Please enter email and password.")
            return

        resp = self.api.call_endpoint("/api/login", {"username": email, "password": pw}, access_token_required=False, login=True)
        if not resp:
            QMessageBox.warning(self, "Login failed", "Could not log in. Check connection or credentials.")
            return

        # Expecting tokens back from API
        print(resp)
        access = resp.get("access_token")
        refresh = resp.get("refresh_token")
        expires_in = resp.get("expires_in", 3600)

        if not access:
            QMessageBox.warning(self, "Login failed", "Server response missing access token.")
            return

        self.api.token.access_token = access
        self.api.token.refresh_token = refresh
        import time
        self.api.token.expiry = time.time() + float(expires_in)
        self.api.token.save_tokens()

        self._choose_online()

    def _do_signup(self):
        email = self.signup_email.text().strip()
        pw = self.signup_password.text().strip()
        name = self.name.text().strip()
        age = self.age.text().strip()
        if not email or not pw:
            QMessageBox.warning(self, "Missing info", "Please enter email and password.")
            return

        resp = self.api.call_endpoint("/api/users", {"artist_name":name, "age":int(age) , "email": email, "password": pw}, access_token_required=False, login=False)
        if not resp:
            print(resp)
            QMessageBox.warning(self, "Sign up failed", "Could not create account. Check connection.")
            return

        print(resp)
        # Often signup returns tokens too. If it doesn’t, you can auto-switch to login tab.
        access = resp.get("access_token")
        refresh = resp.get("refresh_token")
        expires_in = resp.get("expires_in", 3600)

        print(access)
        print(refresh)
        print(expires_in)

        if access:
            self.api.token.access_token = access
            self.api.token.refresh_token = refresh
            import time
            self.api.token.expiry = time.time() + float(expires_in)
            self.api.token.save_tokens()
            self._choose_online()
        else:
            QMessageBox.information(self, "Account created", "Account created. Please log in.")
            self.tabs.setCurrentIndex(0)
