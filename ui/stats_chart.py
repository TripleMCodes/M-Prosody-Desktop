import sys

from PySide6.QtCore import QPointF, QDate
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCharts import QChart, QChartView, QLineSeries


class TestChart(QMainWindow):
    def __init__(self, stats):
        super().__init__()

        self.stats_data = stats
        self.x = 0

        self.series = QLineSeries()
        self.series_2 = QLineSeries()
        # self.series.append(0, 6)
        # self.series.append(2, 4)
        # self.series.append(3, 8)
        # self.series.append(7, 4)
        # self.series.append(10, 5)

        self.series_2.append(0, 2)
        self.series_2.append(2, 4)
        self.series_2.append(3, 6)
        self.series_2.append(7, 8)
        self.series_2.append(10, 10)

        for i in range(0, len(self.stats_data)):
            self.series.append(i, self.stats_data[i][1])
            print(self.stats_data[i][1])
            print(i)

        self.chart = QChart()
        self.chart.legend().hide()

        # for i in range(0, len(self.stats_data)):
        #     self.chart.setAxisX(i)

        self.chart.addSeries(self.series)
        self.chart.addSeries(self.series_2)
        self.chart.createDefaultAxes()
        self.chart.setTitle("Stats Chart")

        self._chart_view = QChartView(self.chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setCentralWidget(self._chart_view)

        # self.load_stats_data()

    def load_stats_data(self):
        # for i in range(0, len(self.stats_data)):
        #     self.series.append(self.stats_data[i][1], i)
        #     print(self.stats_data[i][1])
        #     print(i)
            # print(stat)
            # print(stat[1])
            # print(stat[3])
        self.series.append(0, 6)
        self.series.append(2, 4)
        self.series.append(3, 8)
        self.series.append(7, 4)
        self.series.append(10, 5)

        # for stat in self.stats_data:
        #     self.series_2.append(stat[2], QDate(stat[3]))
            # print(stat)
            # print(stat[2])
            # print(stat[3])

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stats = [(1, 3, 4, '2026-02-19', 1), (2, 3, 4, '2026-02-18', 1), (3, 5, 6, '2026-02-17', 1), (4, 2, 1, '2026-02-16', 1)]

    window = TestChart(stats=stats)
    window.show()
    window.resize(440, 300)
    sys.exit(app.exec())
