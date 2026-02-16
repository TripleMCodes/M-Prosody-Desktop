from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QSizePolicy
)

class NotificationToast(QFrame):
    closed = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.icon = QLabel("✅")
        self.icon.setFixedWidth(20)

        self.msg = QLabel("")
        self.msg.setWordWrap(True)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("GhostBtn")
        self.close_btn.setFixedSize(34, 34)
        self.close_btn.clicked.connect(self.hide_toast)

        layout.addWidget(self.icon)
        layout.addWidget(self.msg, 1)
        layout.addWidget(self.close_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_toast)

    def show_toast(self, message: str, kind: str = "success", ms: int = 2600):
        # kind: "success" | "error" | "info"
        if kind == "error":
            self.icon.setText("⛔")
        elif kind == "info":
            self.icon.setText("ℹ️")
        else:
            self.icon.setText("✅")

        self.msg.setText(message)
        self.setVisible(True)
        self.raise_()

        self._timer.stop()
        self._timer.start(ms)

        # Position bottom-right-ish inside parent
        self._reposition()

    def _reposition(self):
        if not self.parentWidget():
            return
        p = self.parentWidget()
        margin = 18
        w = min(520, max(320, p.width() // 2))
        self.setFixedWidth(w)
        self.adjustSize()
        self.move(p.width() - self.width() - margin, p.height() - self.height() - margin)

    def hide_toast(self):
        self.setVisible(False)
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # keep neat if parent resizes; handled by parent too
