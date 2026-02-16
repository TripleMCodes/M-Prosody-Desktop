from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QSizePolicy
)

# -----------------------------
# Helper: Glass card wrapper
# -----------------------------
def glass_card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    card = QFrame()
    card.setObjectName("GlassCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(10)

    t = QLabel(title)
    t.setObjectName("SectionTitle")
    layout.addWidget(t)

    return card, layout, t