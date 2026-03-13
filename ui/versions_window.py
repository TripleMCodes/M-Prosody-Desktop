from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel
from PySide6.QtCore import Qt

class VersionsWindow(QDialog):
    def __init__(self, versions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Song Versions")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        # List of versions
        self.version_list = QListWidget()
        self.version_list.itemClicked.connect(self.on_version_selected)
        
        for version in versions:
            # version: (id, song_id, version_num, lyrics, created_at, lyrics_hash, hash_algo)
            item_text = f"Version {version[2]} - {version[4]}"  # version num and created_at
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, version)
            self.version_list.addItem(item)
        
        # Text area for lyrics
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        
        self.splitter.addWidget(self.version_list)
        self.splitter.addWidget(self.lyrics_text)
        self.splitter.setSizes([200, 400])
        
        layout.addWidget(self.splitter)
        
        if versions:
            self.version_list.setCurrentRow(0)
            self.on_version_selected(self.version_list.item(0))
    
    def on_version_selected(self, item):
        if item:
            version = item.data(Qt.UserRole)
            self.lyrics_text.setPlainText(version[3])  # lyrics</content>
