from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton


class FloatingTimer(QWidget):
    """Small, draggable, always-on-top timer widget."""

    closed = Signal()

    def __init__(self, parent=None, start_seconds: int = 25 * 60):
        super().__init__(parent)

        # --- state ---
        self.total_seconds = start_seconds
        self.remaining = 0
        self.running = False
        self._drag_offset: QPoint | None = None

        # --- window flags (floating overlay vibes) ---
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # --- UI ---
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        self.label = QLabel(self._format(self.remaining))
        self.label.setStyleSheet("""
            QLabel {
                color: #f5e9ff;
                font-weight: 700;
                font-size: 24px;                  
                padding: 14px 18px;              
                border-radius: 16px;
                /* light neon purple background for visibility */
                background: rgba(180, 0, 255, 180);
                border: 2px solid rgba(200, 100, 255, 200);
                /* a soft but noticeable glow for the neon effect */
                box-shadow: 0 0 12px rgba(200, 100, 255, 160);
            }
        """)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(168, 85, 247, 120);
                border: 1px solid rgba(168, 85, 247, 140);
                border-radius: 10px;
                font-weight: 700;
                color: #f5e9ff;
            }
            QPushButton:hover { background: rgba(199, 125, 255, 150); }
            QPushButton:pressed { background: rgba(124, 58, 237, 160); }
            """)

        self.btn_close.clicked.connect(self._close)

        root.addWidget(self.label)
        root.addWidget(self.btn_close)

        # --- timer driver ---
        self.ticker = QTimer(self)
        self.ticker.setInterval(1000)
        self.ticker.timeout.connect(self._tick)

    # -------- logic --------
    def start(self):
        self.running = True
        self.ticker.start()

    def pause(self):
        self.running = False
        self.ticker.stop()

    # def reset(self):
    #     self.total_seconds = 0
    #     self.label.setText(self._format(self.remaining))

    def set_duration_minutes(self, minutes: int):
        self.total_seconds = max(1, minutes) * 60
        self.reset()

    def _tick(self):
        self.total_seconds += 1
        self.label.setText(self._format(self.total_seconds))

    def _format(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _close(self):
        self.hide()
       
    # -------- drag to move --------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()