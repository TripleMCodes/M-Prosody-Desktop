from __future__ import annotations

from PySide6.QtWidgets import QMessageBox
from ui.auth_dialog import AuthChoiceDialog


class OnlineFeatureGate:
    """
    Central place to decide whether online features are allowed.
    """
    def __init__(self, api, parent_window):
        self.api = api
        self.parent = parent_window
        self.offline_opted = False  # user chose offline explicitly

    def is_logged_in(self) -> bool:
        return bool(self.api.token.is_access_valid())

    def run_startup_prompt_if_needed(self):
        # If user already has a valid token -> do nothing
        if self.is_logged_in():
            self.offline_opted = False
            return

        dlg = AuthChoiceDialog(self.api, parent=self.parent)
        dlg.exec()

        if dlg.result_mode == "online" and self.is_logged_in():
            self.offline_opted = False
        else:
            self.offline_opted = True

    def require_online(self, feature_name: str = "this feature") -> bool:
        """
        Call this before any online-only action.
        Returns True if allowed; False if blocked.
        """
        if self.is_logged_in():
            return True

        # Reminder prompt
        mb = QMessageBox(self.parent)
        mb.setWindowTitle("Online feature")
        mb.setText(f"{feature_name} requires an account.")
        mb.setInformativeText("You’re currently in offline mode. Log in to enable online features.")
        login_btn = mb.addButton("Log in / Sign up", QMessageBox.AcceptRole)
        mb.addButton("Continue offline", QMessageBox.RejectRole)
        mb.exec()

        if mb.clickedButton() == login_btn:
            dlg = AuthChoiceDialog(self.api, parent=self.parent)
            dlg.exec()
            return self.is_logged_in()

        return False
