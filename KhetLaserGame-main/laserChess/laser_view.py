"""
The view manages the user interface.

Classes:

Function:
    main

License:
    MIT License

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
"""

from math import cos, pi, sin
from tracemalloc import start

import numpy as np
from laser_controller import GameController
from laser_model import Color, Orientation
from PyQt5.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen, QTransform
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsView,
    QDialog,
    QWidget,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    # boxes and buttons
    QComboBox,
    QGroupBox,
    QPushButton,
    # layouts
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
)

BOARD_W = 10
BOARD_H = 8


class Scene(QGraphicsScene):
    """Represent the board and the tokens."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.add_client(self)

        self.cellSize = 50
        self.tokenSize = 35
        self.thickness = 5
        self.width = BOARD_W * self.cellSize
        self.height = BOARD_H * self.cellSize
        self.setSceneRect(0, 0, self.width, self.height)

        black = Qt.black
        red = QColor(100, 0, 0)
        gray = Qt.gray
        blue = QColor(0, 0, 100)
        self.color_table = (
            [[black, blue] + [gray] * 6 + [red, blue]]
            + [[red] + [gray] * 8 + [blue]] * 6
            + [[red, blue] + [gray] * 6 + [red, black]]
        )

    def refresh(self):
        """Update the scene."""
        self.clear()
        # Cells
        for i in range(BOARD_H):
            for j in range(BOARD_W):
                cell_color = self.color_table[i][j]
                if self.controller.game.board.squares[i][j].highlighted:
                    cell_color = Qt.lightGray
                if (
                    self.controller.selected_token
                    == self.controller.game.board.squares[i][j].inhabiting_token
                    and self.controller.selected_token
                ):
                    cell_color = Qt.white
                cell = self.addRect(
                    0,
                    0,
                    self.cellSize,
                    self.cellSize,
                    QPen(Qt.black),
                    QBrush(cell_color),
                )
                cell.setPos(j * self.cellSize, i * self.cellSize)
        # Tokens
        for token in self.controller.game.tokens:
            if not token.destroyed:
                self.drawToken(
                    name=token.name,
                    color=token.color,
                    row=token.row,
                    column=token.column,
                    orientation=token.orientation,
                )
        # Laser beam

    def drawLaser(self):
        """Display the laser beam."""
        path = self.controller.game.positions_log

    def drawToken(self, name, color, row, column, orientation=0):
        """Display a laser at the corresponding position.

        color: boolean
            0 is red, 1 is blue
        """
        brush = QBrush(Qt.blue) if color == Color.blue else QBrush(Qt.red)
        black_pen = QPen(Qt.black, self.thickness)
        QtLine, QtPosition = self._tokenRepr(row, column, orientation, name)

        if name == "laser":
            self.addEllipse(QtPosition, pen=black_pen, brush=brush)
            self.addLine(
                self._laserLine(row, column, orientation),
                pen=QPen(brush, self.thickness),
            )
        elif name == "switch":
            self.addLine(QtLine, pen=QPen(brush, self.thickness))
        elif name == "defender":
            self.addRect(QtPosition, pen=black_pen, brush=brush)
            self.addLine(QtLine, pen=QPen(brush, self.thickness))
        elif name == "deflector":
            self.addEllipse(QtPosition, pen=black_pen, brush=brush)
            self.addLine(QtLine, pen=QPen(brush, self.thickness))
        elif name == "queen":
            self.addRect(QtPosition, pen=black_pen, brush=brush)

    def _laserLine(self, r, c, orientation):
        extension = 0.5
        c += 0.5
        r += 0.5
        middle_point = QPointF(c * self.cellSize, r * self.cellSize)
        dict_points = {
            Orientation.right: QPointF(
                (c + extension) * self.cellSize, r * self.cellSize
            ),
            Orientation.up: QPointF(c * self.cellSize, (r - extension) * self.cellSize),
            Orientation.left: QPointF(
                (c - extension) * self.cellSize, r * self.cellSize
            ),
            Orientation.down: QPointF(
                c * self.cellSize, (r + extension) * self.cellSize
            ),
        }
        return QLineF(middle_point, dict_points[orientation])

    def _tokenRepr(self, row, column, orientation, name):
        is_small_token = (name == "defender") or (name == "deflector")
        small_size = self.tokenSize - self.thickness * 2
        QtBigRect = self._tokenRect(row, column, self.tokenSize)
        QtSmallRect = self._tokenRect(row, column, small_size)

        diag = (name == "switch") or (name == "deflector")
        angle = (orientation * 90 - 45) * pi / 180
        offset = [name == "deflector"] * 2
        offset *= small_size // 2 * np.array([-cos(angle), -sin(angle)])

        line_size = small_size if name == "deflector" else self.tokenSize
        corners = self._corners(row, column, line_size, offset)
        if diag:
            p1, p2 = (
                (corners[0], corners[2])
                if orientation.value % 2
                else (corners[1], corners[3])
            )
        else:
            if orientation == Orientation.up:
                p1, p2 = (corners[2], corners[3])
            elif orientation == Orientation.right:
                p1, p2 = corners[1], corners[2]
            elif orientation == Orientation.down:
                p1, p2 = (corners[0], corners[1])
            else:
                p1, p2 = (corners[0], corners[3])
        return (
            QLineF(p1, p2),
            QtSmallRect if is_small_token else QtBigRect,
        )

    def _tokenRect(self, r, c, size, offset=[0, 0]):
        global_offset = (self.cellSize - size) // 2
        QtPosition = QRectF(
            c * self.cellSize + global_offset + offset[1],
            r * self.cellSize + global_offset + offset[0],
            size,
            size,
        )
        return QtPosition

    def _corners(self, r, c, size, offset):
        QtRect = self._tokenRect(r, c, size, offset=offset)
        c = (
            QtRect.bottomLeft(),
            QtRect.bottomRight(),
            QtRect.topRight(),
            QtRect.topLeft(),
        )
        return c

    def mousePressEvent(self, e):
        """Send user click information to the controller."""
        if not self.itemAt(e.scenePos(), QTransform()):
            return
        row = int(e.scenePos().y()) // self.cellSize
        column = int(e.scenePos().x()) // self.cellSize
        self.controller.squareSelected(row, column)
        self.controller.refresh_all("")


class View(QGraphicsView):
    """Control the window size."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.add_client(self)
        self.scene = Scene(self, controller)
        self.setScene(self.scene)

    def resizeEvent(self, event):
        """Resize the window."""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def refresh(self):
        """Update the object."""
        pass


class SidePanel(QWidget):
    """Manages the layout of the parameters (everything but the board)."""

    def __init__(self, parent, controller):
        super().__init__()
        self.controller = controller
        self.controller.add_client(self)
        self.setMinimumWidth(250)

        # Widgets
        self.new_game_button = QPushButton("New game")
        self.AI_test_button = QPushButton("Test AI")
        self.level_box = QComboBox()
        self.rotate_token_groupbox = QGroupBox()
        self.rotate_anticlockwise_button = QPushButton("Rotate anti-clockwise")
        self.rotate_clockwise_button = QPushButton("Rotate clockwise")

        # Layout
        self.formLayout = QFormLayout()

        rotate_token_groupbox_layout = QVBoxLayout()
        self.rotate_token_groupbox.setLayout(rotate_token_groupbox_layout)
        rotate_token_groupbox_layout.addWidget(self.rotate_anticlockwise_button)
        rotate_token_groupbox_layout.addWidget(self.rotate_clockwise_button)
        self.rotate_token_groupbox.setVisible(False)

        # Current player label
        self.current_player_label = QLabel("")

        vLayout = QVBoxLayout()
        vLayout.addLayout(self.formLayout)
        vLayout.addWidget(self.new_game_button)
        vLayout.addWidget(self.AI_test_button)
        vLayout.addWidget(self.current_player_label)
        vLayout.addWidget(self.rotate_token_groupbox)
        vLayout.addStretch()

        self.setLayout(vLayout)

        # Signals
        self.new_game_button.clicked.connect(self.onNewGameButtonClicked)
        self.AI_test_button.clicked.connect(self.on_test_AI)
        self.rotate_anticlockwise_button.clicked.connect(
            self.rotateAntiClockwiseButtonClicked
        )
        self.rotate_clockwise_button.clicked.connect(self.rotateClockwiseButtonClicked)

    def onNewGameButtonClicked(self):
        """Initialise parameters."""
        new_game_setup = newGameSetupWindow(self.controller)
        new_game_setup.exec()
        if new_game_setup.result() == QDialog.Accepted:
            self.controller.start(
                new_game_setup.getRedPlayerType(), new_game_setup.getBluePlayerType()
            )

    def rotateAntiClockwiseButtonClicked(self):
        print("Rotate anti-clockwise")
        self.controller.rotateSelectedTokenAntiClockwise()

    def rotateClockwiseButtonClicked(self):
        print("Rotate clockwise")
        self.controller.rotateSelectedTokenClockwise()

    def on_test_AI(self):
        self.controller.test_AI()

    def refresh(self):
        """Update object."""
        if self.controller.game.turn % 2:
            self.current_player_label.setText("Red player's turn")
        else:
            self.current_player_label.setText("Blue player's turn")

        if self.controller.selected_token:
            if self.controller.selected_token.name == "queen":
                self.rotate_token_groupbox.setVisible(False)
            else:
                self.rotate_token_groupbox.setVisible(True)
        else:
            self.rotate_token_groupbox.setVisible(False)


class newGameSetupWindow(QDialog):
    """New game setup window for choosing player type, etc."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("New game setup")
        self.resize(300, 150)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Player settings
        player_settings_groupbox = QGroupBox()
        player_settings_groupbox_layout = QVBoxLayout()
        player_settings_groupbox.setLayout(player_settings_groupbox_layout)
        main_layout.addWidget(player_settings_groupbox)

        red_player_settings_layout = QHBoxLayout()
        red_player_settings_layout.addWidget(QLabel("Red player"))
        self.red_player_type_combobox = QComboBox()
        self.red_player_type_combobox.addItem("AI")
        self.red_player_type_combobox.addItem("Human")
        red_player_settings_layout.addWidget(self.red_player_type_combobox)
        player_settings_groupbox_layout.addLayout(red_player_settings_layout)

        blue_player_settings_layout = QHBoxLayout()
        blue_player_settings_layout.addWidget(QLabel("Blue player"))
        self.blue_player_type_combobox = QComboBox()
        self.blue_player_type_combobox.addItem("AI")
        self.blue_player_type_combobox.addItem("Human")
        blue_player_settings_layout.addWidget(self.blue_player_type_combobox)
        player_settings_groupbox_layout.addLayout(blue_player_settings_layout)

        # Start button
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        start_button = QPushButton("Start game")
        start_button.setFixedWidth(100)
        start_button.setAutoDefault(True)
        bottom_buttons_layout.addWidget(start_button)
        bottom_buttons_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        main_layout.addLayout(bottom_buttons_layout)

        # Signals
        start_button.clicked.connect(self.startButtonClicked)

    def startButtonClicked(self):
        self.accept()

    def getRedPlayerType(self):
        return self.red_player_type_combobox.currentText()

    def getBluePlayerType(self):
        return self.blue_player_type_combobox.currentText()


class Window(QMainWindow):
    """Main window: Widget plus title."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.controller.add_client(self)
        self.setWindowTitle("Laser chess")

        view = View(self, controller)
        side_panel = SidePanel(self, controller)
        layout = QHBoxLayout()

        layout.addWidget(side_panel)
        layout.addWidget(view)
        mainwidget = QWidget()
        mainwidget.setLayout(layout)

        self.setCentralWidget(mainwidget)

    def refresh(self):
        """Update object."""
        pass


def main():
    """Instanciate necessary classes and display application."""
    app = QApplication([])
    controller = GameController()
    win = Window(controller)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
