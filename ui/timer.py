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
                font-size: 16px;
                padding: 8px 10px;
                border-radius: 12px;
                background: rgba(18, 0, 24, 200);
                border: 1px solid rgba(168, 85, 247, 120);
            }
        """)

        self.btn_start = QPushButton("▶")
        self.btn_pause = QPushButton("⏸")
        self.btn_reset = QPushButton("↺")
        self.btn_close = QPushButton("✕")

        for b in (self.btn_start, self.btn_pause, self.btn_reset, self.btn_close):
            b.setFixedSize(32, 32)
            b.setStyleSheet("""
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

        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_close.clicked.connect(self._close)

        root.addWidget(self.label)
        root.addWidget(self.btn_start)
        root.addWidget(self.btn_pause)
        root.addWidget(self.btn_reset)
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

    def reset(self):
        self.total_seconds = 0
        self.label.setText(self._format(self.remaining))

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
        self.pause()
        self.hide()
        self.closed.emit()

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