import sys
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PySide6.QtCore import QThread, Signal
from pathlib import Path


class RecorderThread(QThread):
    finished = Signal(str)

    def __init__(self, duration=0, samplerate=44100, song_title="recording.wav"):
        super().__init__()
        self.duration = duration
        self.samplerate = samplerate
        self.recording = []
        self.running = False
        self.song_title = song_title
        self.base_path = Path(__file__).parent

    def run(self):
        self.running = True
        # Record until stopped
        with sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.callback):
            while self.running:
                sd.sleep(100)

        # Save to WAV
        filename = self.base_path / f"{self.song_title}.wav"
        audio_data = np.concatenate(self.recording, axis=0)
        write(filename, self.samplerate, audio_data)
        self.finished.emit(filename)

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recording.append(indata.copy())

    def stop(self):
        self.running = False

    


class VoiceRecorder(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Melody & Flow Recorder")
        self.setGeometry(300, 300, 300, 200)
        qss_style = ("""
                QWidget {
                    background-color: #3b2a4d; /* deep muted purple */
                    color: #e5d4ff; /* light lavender text */
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 14px;
                }

                QLineEdit {
                    background-color: #4b3b5f;
                    border: 2px solid #6a4fa3;
                    border-radius: 6px;
                    padding: 6px;
                    color: #f5ebff;
                    selection-background-color: #8b5cf6; /* soft purple highlight */
                }

                QLineEdit:focus {
                    border: 2px solid #b58fff;
                    background-color: #56436f;
                }

                QLabel {
                    color: #e0c8ff;
                    font-size: 15px;
                }

                QPushButton {
                    background-color: #6a4fa3;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                }

                QPushButton:hover {
                    background-color: #7e62c0;
                }

                QPushButton:pressed {
                    background-color: #523a80;
                }

                QPushButton:disabled {
                    background-color: #403255;
                    color: #a28dbf;
                }
            """)

        
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setStyleSheet(qss_style)
        
        self.song_title_box = QLineEdit()
        self.song_title_box.setPlaceholderText("Enter record title")

        self.label = QLabel("Press record to start")

        layout.addWidget(self.song_title_box)
        layout.addWidget(self.label)

        self.btn_record = QPushButton("🎙️ Record")
        self.btn_stop = QPushButton("⏹️ Stop")
        self.btn_stop.setEnabled(False)

        layout.addWidget(self.btn_record)
        layout.addWidget(self.btn_stop)

        self.recorder_thread = None

        self.btn_record.clicked.connect(self.start_recording)
        self.btn_stop.clicked.connect(self.stop_recording)

    def start_recording(self):
        self.label.setText("Recording... 🎵")
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)

        song_tile = self.get_song_title()
        self.recorder_thread = RecorderThread(song_title=song_tile)
        self.recorder_thread.finished.connect(self.on_finished)
        self.recorder_thread.start()

    def stop_recording(self):
        self.label.setText("Stopping...")
        self.btn_stop.setEnabled(False)
        if self.recorder_thread:
            self.recorder_thread.stop()

    def get_song_title(self):
        title =  self.song_title_box.text().strip()
        return title

    def on_finished(self):
        filename = self.get_song_title()
        self.label.setText(f"Saved: {filename}")
        self.btn_record.setEnabled(True)
        self.song_title_box.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceRecorder()
    window.show()
    sys.exit(app.exec())
