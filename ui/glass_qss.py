GLASS_QSS = """
/* ===== Theme vars-ish ===== */
QWidget {
    font-family: "Segoe UI";
    color: #f5e9ff;
}

/* Container background can be set by parent app stylesheet; this focuses on the cards */
QFrame#GlassPanel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(120, 50, 180, 64),
        stop:1 rgba(25, 8, 40, 140)
    );
    border-radius: 22px;
    border: 1px solid rgba(168, 85, 247, 64);
    padding: 18px;
}

QFrame#GlassCard {
    background: rgba(40, 10, 60, 115);
    border-radius: 18px;
    border: 1px solid rgba(168, 85, 247, 55);
    padding: 14px;
}

QLabel#SectionTitle {
    font-size: 16px;
    font-weight: 600;
}

QLineEdit, QTextEdit {
    background: rgba(18, 0, 24, 160);
    border: 1px solid rgba(168, 85, 247, 55);
    border-radius: 12px;
    padding: 10px;
    selection-background-color: rgba(168, 85, 247, 120);
}

QTextEdit {
    min-height: 90px;
}

QPushButton {
    background: rgba(168, 85, 247, 120);
    border: 1px solid rgba(168, 85, 247, 140);
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 600;
}

QPushButton:hover {
    background: rgba(199, 125, 255, 150);
}

QPushButton:pressed {
    background: rgba(124, 58, 237, 160);
}

QPushButton#GhostBtn {
    background: transparent;
    border: 1px solid rgba(168, 85, 247, 90);
}

QListWidget {
    background: rgba(18, 0, 24, 120);
    border: 1px solid rgba(168, 85, 247, 55);
    border-radius: 12px;
    padding: 6px;
}

QListWidget::item {
    padding: 10px;
    margin: 4px;
    border-radius: 10px;
}

QListWidget::item:selected {
    background: rgba(168, 85, 247, 120);
}

/* Notification toast */
QFrame#Toast {
    background: rgba(18, 0, 24, 210);
    border: 1px solid rgba(168, 85, 247, 120);
    border-radius: 14px;
    padding: 12px 14px;
}
"""
