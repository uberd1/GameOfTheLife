import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QTimer, QRect, QPoint


class GridWidget(QWidget):
    def __init__(self, size=50, parent=None):
        super().__init__(parent)
        self.size = size
        self.setMinimumSize(500, 500)
        self.glider_pattern = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
        # вектор глайдера
        self.grid = []
        self.clear_grid()

    def clear_grid(self):
        self.grid = []
        for el in range(self.size):
            row = [0] * self.size
            self.grid.append(row)
        self.update()

    def randomize_glider(self):
        self.clear_grid()
        max_pos = self.size - 3
        rand_row = random.randint(0, max_pos)
        rand_col = random.randint(0, max_pos)
        for deltrow, deltcol in self.glider_pattern:
            self.grid[rand_row + deltrow][rand_col + deltcol] = 1
        # закрашиваем точки из glider pattern по сравнению с рандомной
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        cell_width = self.width() / self.size
        cell_height = self.height() / self.size
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 1:
                    pos_x = int(j * cell_width)
                    pos_y = int(i * cell_height)
                    width = int(cell_width)
                    height = int(cell_height)
                    rect = QRect(pos_x, pos_y, width, height)
                    painter.fillRect(rect, QColor("black"))
        # Вторая часть кода, рисуем тетрадные клеточки
        pen = QPen(QColor("#dcdcdc"))
        pen.setWidth(1)
        painter.setPen(pen)
        # Рисуем вертикальные линии
        for j in range(self.size + 1):
            x = int(j * cell_width)
            painter.drawLine(x, 0, x, self.height())
        # Рисуем горизонтальные линии
        for i in range(self.size + 1):
            y = int(i * cell_height)
            painter.drawLine(0, y, self.width(), y)

    def mousePressEvent(self, event):
        cell_width = self.width() / self.size
        cell_height = self.height() / self.size
        if cell_height == 0 or cell_height == 0: return
        pos = event.position()
        j = int(pos.x() / cell_width)
        i = int(pos.y() / cell_height)
        if 0 <= i < self.size and 0 <= j < self.size:
            self.grid[i][j] = 1 - self.grid[i][j]
            self.update()

    def neighborhood(self, x, y):
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0: continue
                vx = (x + i) % self.size
                vy = (y + j) % self.size
                # % self.size это попытка создать бесконечное поле когда при уходе влево фигура появляется справа как в
                # в бублике или пончике 🥯🥯🥯
                count += self.grid[vx][vy]
        return count

    def update_grid(self):
        temp_grid = []
        for row in self.grid:
            temp_row = row[:]
            temp_grid.append(temp_row)
        for i in range(self.size):
            for j in range(self.size):
                neighbors = self.neighborhood(i, j)
                if self.grid[i][j] == 1:
                    if neighbors < 2 or neighbors > 3:
                        temp_grid[i][j] = 0
                else:
                    if neighbors == 3:
                        temp_grid[i][j] = 1
        self.grid = temp_grid
        self.update()


class GameOfLifeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game of Life")
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.grid_widget = GridWidget(size=50)
        main_layout.addWidget(self.grid_widget)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_game)
        button_layout.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_game)
        button_layout.addWidget(stop_button)

        glider_random_button = QPushButton("Randomize Glider")
        glider_random_button.clicked.connect(self.randomize_glider)
        button_layout.addWidget(glider_random_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)
        button_layout.addWidget(clear_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.grid_widget.update_grid)

    def start_game(self):
        self.timer.start(100)

    def stop_game(self):
        self.timer.stop()

    def randomize_glider(self):
        self.stop_game()
        self.grid_widget.randomize_glider()

    def clear(self):
        self.stop_game()
        self.grid_widget.clear_grid()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameOfLifeWindow()
    window.show()
    sys.exit(app.exec())
