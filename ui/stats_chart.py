from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Tuple, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QDateTimeAxis,
    QValueAxis,
    QLineSeries,
)
from PySide6.QtCore import QDateTime

@dataclass(frozen=True)
class WritingStatRow:
    writing_time: int  
    sessions: int
    created_at: date


class WritingStatsChart(QWidget):
    """
    Charts:
      - Sessions per day (left Y axis)
      - Writing time per day (right Y axis)
    X axis: date
    """

    def __init__(self, stats):
        super().__init__()

        self.title = QLabel("Writing Stats (Sessions & Writing Time)")
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.chart_view)

        # Series
        self.series_sessions = QLineSeries()
        self.series_sessions.setName("Sessions")

        self.series_time = QLineSeries()
        self.series_time.setName("Writing Time")

        # Axes
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("yyyy-MM-dd")
        self.axis_x.setTitleText("Date")

        self.axis_y_left = QValueAxis()
        self.axis_y_left.setTitleText("Sessions")
        self.axis_y_left.setLabelFormat("%d")
        self.axis_y_left.setMin(0)

        self.axis_y_right = QValueAxis()
        self.axis_y_right.setTitleText("Writing Time")
        self.axis_y_right.setLabelFormat("%d")
        self.axis_y_right.setMin(0)

        # Put chart together
        self.chart.addSeries(self.series_sessions)
        self.chart.addSeries(self.series_time)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y_left, Qt.AlignLeft)
        self.chart.addAxis(self.axis_y_right, Qt.AlignRight)

        self.series_sessions.attachAxis(self.axis_x)
        self.series_sessions.attachAxis(self.axis_y_left)

        self.series_time.attachAxis(self.axis_x)
        self.series_time.attachAxis(self.axis_y_right)

        self.stats = stats

        # Initial render
        self.refresh()

    def fetch_data(self, local_profile_id: int = 1) -> List[WritingStatRow]:
        raw_rows = self.stats.get_stats()

        rows: List[WritingStatRow] = []
        for _id, writing_time, sessions, created_at, pid in raw_rows:
            if pid != local_profile_id:
                continue
            d = datetime.strptime(created_at, "%Y-%m-%d").date()
            rows.append(WritingStatRow(writing_time=writing_time, sessions=sessions, created_at=d))

        # sort by date ascending for a nice line
        rows.sort(key=lambda r: r.created_at)
        return rows

    # Chart rendering
    def refresh(self, local_profile_id: int = 1):
        rows = self.fetch_data(local_profile_id=local_profile_id)

        # Clear old points
        self.series_sessions.clear()
        self.series_time.clear()

        if not rows:
            self.chart.setTitle("No data")
            return

        # Convert dates to milliseconds since epoch via QDateTime
        # Use noon time to avoid DST edge weirdness
        xs: List[QDateTime] = []
        max_sessions = 0
        max_time = 0

        for r in rows:
            qdt = QDateTime(r.created_at.year, r.created_at.month, r.created_at.day, 12, 0, 0)
            x = qdt.toMSecsSinceEpoch()
            xs.append(qdt)

            self.series_sessions.append(x, r.sessions)
            self.series_time.append(x, r.writing_time)

            max_sessions = max(max_sessions, r.sessions)
            max_time = max(max_time, r.writing_time)

        # X range
        self.axis_x.setRange(xs[0], xs[-1])

        # Y ranges with a little headroom
        self.axis_y_left.setMax(max(1, int(max_sessions * 1.2)))
        self.axis_y_right.setMax(max(1, int(max_time * 1.2)))

        self.chart.setTitle("Writing Stats")