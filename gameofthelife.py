import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen, QIcon
from PyQt6.QtCore import QTimer, QRectF, Qt


# --- Класс игрового поля ---
# Отвечает за всю логику, отрисовку и обработку пользовательского ввода.
class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)

        # Для "бесконечного" поля используется множество (set) для хранения координат
        # только живых клеток в формате (колонка, ряд).
        self.live_cells = set()

        # Шаблон фигуры "Глайдер" в виде смещений (ряд, колонка).
        self.glider_pattern = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

        # --- Система курсора ---
        self.cursor_pos = (0, 0)  # Текущие мировые координаты курсора (колонка, ряд).
        self.cursor_visible = True  # Флаг для организации мигания.

        # Отдельный таймер, который отвечает только за мигание курсора.
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor_visibility)
        self.cursor_timer.start(500)  # Интервал мигания - 500 мс.

        # --- Система "Камеры" ---
        self.zoom = 10.0  # Масштаб (размер одной клетки в пикселях).
        self.offset_x = 0  # Смещение вида по горизонтали (панорамирование).
        self.offset_y = 0  # Смещение вида по вертикали.

        # --- Система перетаскивания поля ---
        self.panning = False  # Флаг, активен ли режим перетаскивания.
        self.last_mouse_pos = None  # Хранит последнюю позицию мыши при перетаскивании.

    def _toggle_cursor_visibility(self):
        """Инвертирует видимость курсора для создания эффекта мигания."""
        self.cursor_visible = not self.cursor_visible
        self.update()  # Запрашивает перерисовку для обновления вида курсора.

    def showEvent(self, event):
        """
        Этот метод вызывается один раз, когда виджет впервые отображается.
        Используется для корректной инициализации смещения камеры в центр экрана.
        """
        super().showEvent(event)
        if self.offset_x == 0 and self.offset_y == 0:
            self.offset_x = self.width() / 2
            self.offset_y = self.height() / 2

    def clear_grid(self):
        """Полностью очищает поле от живых клеток."""
        self.live_cells.clear()
        self.update()

    def reset_and_center_glider(self):
        """Сбрасывает вид и ставит глайдер в центре координат (0,0)."""
        self.clear_grid()
        self.zoom = 10.0
        self.offset_x = self.width() / 2
        self.offset_y = self.height() / 2

        # Размещаем глайдер относительно мировой точки (0,0).
        for dr, dc in self.glider_pattern:
            self.live_cells.add((0 + dc, 0 + dr))
        self.update()

    def screen_to_world(self, pos):
        """Преобразует экранные координаты (пиксели) в мировые (клетки)."""
        col = int((pos.x() - self.offset_x) / self.zoom)
        row = int((pos.y() - self.offset_y) / self.zoom)
        return col, row

    def count_neighbors(self, col, row):
        """Считает количество живых соседей для указанной клетки."""
        count = 0
        # dr (delta row) и dc (delta col) - смещения для проверки 8 соседей.
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue  # Пропускаем саму клетку.
                if (col + dc, row + dr) in self.live_cells:
                    count += 1
        return count

    def update_grid(self):
        """Вычисляет следующее поколение клеток по правилам игры 'Жизнь'."""
        # Собираем всех "кандидатов" - живые клетки и их непосредственных соседей.
        # Только эти клетки могут изменить свое состояние.
        candidates = set()
        for (col, row) in self.live_cells:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    candidates.add((col + dc, row + dr))

        next_live_cells = set()
        # Проверяем каждого кандидата и решаем, будет ли он жив в след. поколении.
        for (col, row) in candidates:
            neighbors = self.count_neighbors(col, row)
            is_alive = (col, row) in self.live_cells

            if (is_alive and neighbors in (2, 3)) or (not is_alive and neighbors == 3):
                next_live_cells.add((col, row))

        self.live_cells = next_live_cells
        self.update()

    def keyPressEvent(self, event):
        """Обрабатывает нажатия клавиш для управления курсором и клетками."""
        col, row = self.cursor_pos

        # Движение курсора стрелками.
        if event.key() == Qt.Key.Key_Up:
            row -= 1
        elif event.key() == Qt.Key.Key_Down:
            row += 1
        elif event.key() == Qt.Key.Key_Left:
            col -= 1
        elif event.key() == Qt.Key.Key_Right:
            col += 1
        # Нажатие Enter инвертирует состояние клетки под курсором.
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.cursor_pos in self.live_cells:
                self.live_cells.remove(self.cursor_pos)
            else:
                self.live_cells.add(self.cursor_pos)
        elif event.key() == Qt.Key.Key_End:
            # Дебаг функция для проверки заполненности поля

            # 1. Вычисляем, какие координаты сейчас видны на экране.
            start_col = int(-self.offset_x / self.zoom)
            end_col = int((-self.offset_x + self.width()) / self.zoom) + 1
            start_row = int(-self.offset_y / self.zoom)
            end_row = int((-self.offset_y + self.height()) / self.zoom) + 1

            # 2. Очищаем поле от всех предыдущих клеток.
            self.live_cells.clear()

            # 3. Проходим по каждой видимой клетке и с 50% шансом "оживляем" ее.
            for col in range(start_col, end_col):
                for row in range(start_row, end_row):
                    if random.choice([True, False]):
                        self.live_cells.add((col, row))

            # 4. Показаваем результат.
            self.update()
        self.cursor_pos = (col, row)
        self.cursor_visible = True  # Делаем курсор видимым после любого действия.
        self.cursor_timer.start(500)  # Перезапускаем таймер мигания.
        self.update()

    def mousePressEvent(self, event):
        """Обрабатывает нажатия кнопок мыши."""
        # Левая кнопка: перемещает курсор в указанную точку.
        if event.button() == Qt.MouseButton.LeftButton:
            self.cursor_pos = self.screen_to_world(event.position())
            self.cursor_visible = True
            self.cursor_timer.start(500)
            self.update()
        # Правая кнопка: активирует режим перетаскивания поля.
        elif event.button() == Qt.MouseButton.RightButton:
            self.panning = True
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        """Обрабатывает движение мыши, если режим перетаскивания активен."""
        if self.panning:
            delta = event.position() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        """Отключает режим перетаскивания, когда правая кнопка отпущена."""
        if event.button() == Qt.MouseButton.RightButton:
            self.panning = False
            self.last_mouse_pos = None

    def wheelEvent(self, event):
        """Обрабатывает прокрутку колеса мыши для изменения масштаба."""
        old_zoom = self.zoom
        mouse_pos = event.position()

        # Вычисляем мировые координаты под курсором до изменения масштаба.
        world_before_zoom_x = (mouse_pos.x() - self.offset_x) / old_zoom
        world_before_zoom_y = (mouse_pos.y() - self.offset_y) / old_zoom

        # Изменяем масштаб.
        if event.angleDelta().y() > 0:
            self.zoom *= 1.2
        else:
            self.zoom /= 1.2
        self.zoom = max(1, min(self.zoom, 100))  # Ограничиваем масштаб.

        # Корректируем смещение, чтобы точка под курсором осталась на месте.
        self.offset_x = mouse_pos.x() - world_before_zoom_x * self.zoom
        self.offset_y = mouse_pos.y() - world_before_zoom_y * self.zoom
        self.update()

    def paintEvent(self, event):
        """Главный метод отрисовки. Вызывается каждый раз при self.update()."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))  # Заливаем фон белым.

        # Вычисляем, какие мировые координаты (клетки) сейчас видны на экране.
        start_col = int(-self.offset_x / self.zoom);
        end_col = int((-self.offset_x + self.width()) / self.zoom) + 1
        start_row = int(-self.offset_y / self.zoom);
        end_row = int((-self.offset_y + self.height()) / self.zoom) + 1

        # Рисуем сетку, только если масштаб достаточно большой.
        if self.zoom > 4:
            pen = QPen(QColor("#dcdcdc"));
            pen.setWidth(1);
            painter.setPen(pen)
            for x in range(start_col, end_col): painter.drawLine(int(x * self.zoom + self.offset_x), 0,
                                                                 int(x * self.zoom + self.offset_x), self.height())
            for y in range(start_row, end_row): painter.drawLine(0, int(y * self.zoom + self.offset_y), self.width(),
                                                                 int(y * self.zoom + self.offset_y))

        # Рисуем все живые клетки, которые попадают в видимую область.
        painter.setBrush(QColor("black"));
        painter.setPen(Qt.PenStyle.NoPen)
        for (col, row) in self.live_cells:
            if start_col <= col < end_col and start_row <= row < end_row:
                painter.drawRect(
                    QRectF(col * self.zoom + self.offset_x, row * self.zoom + self.offset_y, self.zoom, self.zoom))

        # Рисуем мигающий курсор поверх всего остального.
        if self.cursor_visible:
            col, row = self.cursor_pos
            if start_col <= col < end_col and start_row <= row < end_row:
                pen = QPen(QColor("red"));
                pen.setWidth(2);
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)  # Прозрачная заливка.
                painter.drawRect(
                    QRectF(col * self.zoom + self.offset_x, row * self.zoom + self.offset_y, self.zoom, self.zoom))


# --- Класс главного окна ---
# Отвечает за создание окна, кнопок и компоновку элементов.
class GameOfLifeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle("Game of Life")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.grid_widget = GridWidget()
        # Разрешаем виджету отслеживать нажатия клавиш.
        self.grid_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        main_layout.addWidget(self.grid_widget)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Создание и подключение кнопок управления.
        start_button = QPushButton("Start");
        start_button.clicked.connect(self.start_game)
        stop_button = QPushButton("Stop");
        stop_button.clicked.connect(self.stop_game)
        reset_glider_button = QPushButton("Reset & Center Glider")
        reset_glider_button.clicked.connect(self.reset_glider)
        clear_button = QPushButton("Clear");
        clear_button.clicked.connect(self.clear)

        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(reset_glider_button)
        button_layout.addWidget(clear_button)

        # Главный таймер, отвечающий за симуляцию.
        self.timer = QTimer();
        self.timer.timeout.connect(self.grid_widget.update_grid)

    def start_game(self): self.timer.start(100)

    def stop_game(self): self.timer.stop()

    def reset_glider(self):
        self.stop_game()
        self.grid_widget.reset_and_center_glider()

    def clear(self):
        self.stop_game()
        self.grid_widget.clear_grid()


# --- Точка входа в приложение ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameOfLifeWindow()
    window.show()
    sys.exit(app.exec())