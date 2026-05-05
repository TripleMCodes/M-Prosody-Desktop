"""
ui/update_dialog.py — Update Dialog for MProsody
=================================================
A polished, non-blocking update UI that runs the updater
in a background thread so the GUI never freezes.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QPropertyAnimation,
    QEasingCurve, QTimer, QPoint
)
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient


# ── Worker thread ─────────────────────────────────────────────────────────────

class UpdateWorker(QThread):
    """Runs the download + install in a background thread."""

    progress       = Signal(int)      # 0–100
    status_changed = Signal(str)      # human-readable status line
    finished       = Signal(bool)     # True = success, False = failed/skipped

    def __init__(self, version_info: dict, parent=None):
        super().__init__(parent)
        self.version_info = version_info

    def run(self):
        import tempfile
        import shutil
        from pathlib import Path
        from updater import download_update, backup_current_app, install_update, APP_DIR

        download_url = self.version_info["download_url"]

        self.status_changed.emit("Creating backup…")
        self.progress.emit(10)
        try:
            backup_dir = backup_current_app(APP_DIR)
        except Exception as e:
            self.status_changed.emit(f"Backup failed: {e}")
            self.finished.emit(False)
            return

        self.status_changed.emit("Downloading update…")

        with tempfile.TemporaryDirectory() as tmp:
            zip_path = None

            def _on_progress(block_count, block_size, total_size):
                if total_size > 0:
                    downloaded = min(block_count * block_size, total_size)
                    pct = int(downloaded / total_size * 70) + 20   # 20–90 range
                    self.progress.emit(pct)

            import urllib.request
            try:
                zip_path, _ = urllib.request.urlretrieve(
                    download_url,
                    Path(tmp) / download_url.split("/")[-1],
                    reporthook=_on_progress,
                )
            except Exception as e:
                self.status_changed.emit(f"Download failed: {e}")
                self.finished.emit(False)
                return

            self.status_changed.emit("Installing…")
            self.progress.emit(92)

            success = install_update(Path(zip_path), APP_DIR)

            if not success:
                from updater import restore_backup
                restore_backup(backup_dir, APP_DIR)
                self.status_changed.emit("Install failed — rolled back.")
                self.finished.emit(False)
                return

        self.progress.emit(100)
        self.status_changed.emit("Update complete!")
        self.finished.emit(True)


# ── Dialog ────────────────────────────────────────────────────────────────────

class UpdateDialog(QDialog):
    """
    Shows when a new version is available.

    Two modes:
      • "available"  — asks user to update now or skip
      • "progress"   — shows download/install progress bar
      • "done"       — success or failure message + restart / close button
    """

    update_applied = Signal()   # emitted after successful install

    # ── dark, editorial palette ───────────────────────────────────────────────
    BG          = "#0e0e12"
    SURFACE     = "#16161d"
    BORDER      = "#2a2a38"
    ACCENT      = "#7c6af7"        # soft violet
    ACCENT2     = "#c084fc"        # lavender highlight
    TEXT_PRI    = "#e8e6f0"
    TEXT_SEC    = "#7a7890"
    SUCCESS     = "#4ade80"
    DANGER      = "#f87171"

    def __init__(self, version_info: dict, current_version: str, parent=None):
        super().__init__(parent)
        self.version_info    = version_info
        self.current_version = current_version
        self.worker          = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 300)
        self._drag_pos = None

        self._build_ui()
        self._apply_styles()
        self._fade_in()

    # ── drag support (frameless) ──────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Card container
        self.card = QWidget()
        self.card.setObjectName("card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 32, 36, 28)
        card_layout.setSpacing(0)
        root.addWidget(self.card)

        # ── Header row ────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(0)

        badge = QLabel("UPDATE")
        badge.setObjectName("badge")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.reject)

        header.addWidget(badge)
        header.addStretch()
        header.addWidget(close_btn)
        card_layout.addLayout(header)
        card_layout.addSpacing(20)

        # ── Version headline ──────────────────────────────────────────────────
        remote = self.version_info.get("version", "?")
        self.headline = QLabel(f"v{remote} is ready")
        self.headline.setObjectName("headline")
        card_layout.addWidget(self.headline)
        card_layout.addSpacing(6)

        # ── Sub-label ─────────────────────────────────────────────────────────
        self.sub = QLabel(
            f"You're on v{self.current_version}   ·   "
            + (self.version_info.get("release_notes") or "Performance improvements and bug fixes.")
        )
        self.sub.setObjectName("sub")
        self.sub.setWordWrap(True)
        card_layout.addWidget(self.sub)
        card_layout.addSpacing(24)

        # ── Progress bar (hidden until download starts) ───────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("pbar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("progress_label")
        self.progress_label.hide()
        card_layout.addWidget(self.progress_label)
        card_layout.addSpacing(8)

        card_layout.addStretch()

        # ── Button row ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.skip_btn = QPushButton("Skip for now")
        self.skip_btn.setObjectName("skip_btn")
        self.skip_btn.clicked.connect(self.reject)

        self.update_btn = QPushButton("Download & Install  →")
        self.update_btn.setObjectName("update_btn")
        self.update_btn.clicked.connect(self._start_update)

        btn_row.addWidget(self.skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.update_btn)
        card_layout.addLayout(btn_row)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: transparent;
            }}

            #card {{
                background: {self.BG};
                border: 1px solid {self.BORDER};
                border-radius: 16px;
            }}

            #badge {{
                background: {self.ACCENT};
                color: #fff;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2.5px;
                padding: 3px 10px;
                border-radius: 20px;
            }}

            #close_btn {{
                background: transparent;
                color: {self.TEXT_SEC};
                border: none;
                font-size: 13px;
                border-radius: 14px;
            }}
            #close_btn:hover {{
                background: {self.SURFACE};
                color: {self.TEXT_PRI};
            }}

            #headline {{
                font-family: 'Georgia', 'Times New Roman', serif;
                font-size: 26px;
                font-weight: 700;
                color: {self.TEXT_PRI};
                letter-spacing: -0.5px;
            }}

            #sub {{
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 11px;
                color: {self.TEXT_SEC};
                line-height: 1.6;
            }}

            #pbar {{
                background: {self.SURFACE};
                border: none;
                border-radius: 2px;
            }}
            #pbar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.ACCENT}, stop:1 {self.ACCENT2}
                );
                border-radius: 2px;
            }}

            #progress_label {{
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 10px;
                color: {self.TEXT_SEC};
                margin-top: 4px;
            }}

            #skip_btn {{
                background: transparent;
                color: {self.TEXT_SEC};
                border: 1px solid {self.BORDER};
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 12px;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
            }}
            #skip_btn:hover {{
                border-color: {self.ACCENT};
                color: {self.TEXT_PRI};
            }}

            #update_btn {{
                background: {self.ACCENT};
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'JetBrains Mono', 'Courier New', monospace;
            }}
            #update_btn:hover {{
                background: {self.ACCENT2};
            }}
            #update_btn:disabled {{
                background: {self.BORDER};
                color: {self.TEXT_SEC};
            }}
        """)

    def _fade_in(self):
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(220)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    # ── Update flow ───────────────────────────────────────────────────────────

    def _start_update(self):
        self.update_btn.setDisabled(True)
        self.skip_btn.setDisabled(True)
        self.update_btn.setText("Installing…")

        self.progress_bar.show()
        self.progress_label.show()
        self.progress_label.setText("Preparing…")

        self.worker = UpdateWorker(self.version_info, parent=self)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status_changed.connect(self.progress_label.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success: bool):
        if success:
            self.headline.setText("All done! ✦")
            self.sub.setText("The update was installed. Restart to use the new version.")
            self.progress_label.setText("Complete")
            self.progress_label.setStyleSheet(f"color: {self.SUCCESS};")
            self.update_btn.setText("Restart now")
            self.update_btn.setDisabled(False)
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self._restart)
            self.skip_btn.setText("Later")
            self.skip_btn.setDisabled(False)
            self.update_applied.emit()
        else:
            self.headline.setText("Update failed")
            self.sub.setText("Something went wrong. Your app was rolled back to the previous version.")
            self.progress_label.setStyleSheet(f"color: {self.DANGER};")
            self.update_btn.setText("Close")
            self.update_btn.setDisabled(False)
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self.reject)
            self.skip_btn.hide()

    def _restart(self):
        self.accept()
        from updater import relaunch_app
        relaunch_app()
