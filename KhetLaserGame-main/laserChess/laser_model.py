"""
The model manages the data, logic and rules of the application.

Classes:

License:
    MIT License

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""

import enum
import warnings

import numpy as np


class Color(enum.Enum):
    """The different colors used in the game (for squares, tokens and players)."""

    none = 0
    blue = 1
    red = 2


class Orientation(enum.IntEnum):
    """See comments for switches and deflectors."""

    right = 0  # \
    up = 1  # /
    left = 2  # \
    down = 3  # /


class Player:
    """Player of the game"""

    def __init__(self, color, name):
        self.color = color
        self.name = name


class AI(Player):
    """Define and use searches strategies.

    Depth limited minmax, alpha beta pruning, maybe monte carlo.
    """

    def __init__(self, game, color, depth_limit=1):
        super().__init__(color, "AI")
        self.game = game
        self.adversial_color = Color.blue if self.color is Color.red else Color.red
        self.depth_limit = depth_limit

        tokens = game.tokens
        self.names = np.array([t.name for t in tokens])
        self.colors = np.array([t.color for t in tokens])
        self.queen_index = dict()
        for color in [Color.blue, Color.red]:
            self.queen_index[color] = np.argwhere(
                (self.names == "queen") & (self.colors == color)
            )[0][0]

    def minimax(self, depth=0, max_plays=True, alpha=-2e10, beta=2e10, verbose=False):
        """Consider the game tree up to a given depth and decide of the next action."""
        if depth > self.depth_limit:
            return self.evaluate_state()
        if max_plays:
            possible_actions = self.game.getAllPossibleActions(self.color)
            max_evaluation = -2e10
            for action in possible_actions:
                if verbose:
                    print("Considering action:", action)
                self.game.doAction(action)
                self.game.activate_laser(self.color)
                evaluation = self.minimax(depth + 1, (not max_plays), alpha, beta)
                if verbose:
                    print("Eval:", evaluation)
                self.game.undoLastEvent()
                if evaluation > max_evaluation:
                    max_evaluation = evaluation
                    best_action = action
                alpha = max(alpha, evaluation)
                if beta < alpha:
                    break
            final_eval = max_evaluation

        else:
            possible_actions = self.game.getAllPossibleActions(self.adversial_color)
            min_evaluation = 2e10
            for action in possible_actions:
                self.game.doAction(action)
                self.game.activate_laser(self.adversial_color)
                evaluation = self.minimax(depth + 1, (not max_plays), alpha, beta)
                self.game.undoLastEvent()
                if evaluation < min_evaluation:
                    min_evaluation = evaluation
                    best_action = action
                beta = min(beta, evaluation)
                if beta < alpha:
                    break
            final_eval = min_evaluation

        if depth == 0:
            if verbose:
                print("Evaluation:", self.evaluate_state())
            return best_action
        else:
            return final_eval

    def evaluate_state(self):
        """Return a simple estimate of the strategic advantage of the board."""
        tokens = self.game.tokens
        if tokens[self.queen_index[self.color]].destroyed:
            return -1e10
        elif tokens[self.queen_index[self.adversial_color]].destroyed:
            return 1e10

        value = 0

        for defender in tokens[self.names == "defender"]:
            if not defender.destroyed:
                f = 1 if defender.color == self.color else -1
                value += f * 1e4 / self.distance_to_queen(defender, tokens)
        for deflector in tokens[self.names == "deflector"]:
            if not deflector.destroyed:
                f = 1 if deflector.color == self.color else -1
                value += f * 7.5e4
            # TODO increase when we send laser into field
        return value  # + np.random.uniform()

    def distance_to_queen(self, token, tokens):
        """Return the Manhattan distance to the queen of the same color."""
        queen = tokens[self.queen_index[token.color]]
        distance = np.abs(token.row - queen.row) + np.abs(token.column - queen.column)
        if (token.row == queen.row) & (token.column == queen.column):
            warnings.warn("Defender and Queen at the same position")
        return max(1, distance)


class Game:
    """The game.

    Parameters
    ----------
    board: Board

    tokens: Token[]

    lasers: Laser[]

    players: Player[]

    current_player: int
        0 is the first player and 1 is the second player
    """

    def __init__(self):
        self.board = Board()
        self.log = []
        self.red_laser = Laser(0, 0, Color.red, Orientation.down)
        self.blue_laser = Laser(7, 9, Color.blue, Orientation.up)
        self.laser_dict = {Color.blue: self.blue_laser, Color.red: self.red_laser}
        self.turn = 0
        self.tokens = np.array(
            [
                # red team
                self.red_laser,
                Queen(0, 5, Color.red),
                Defender(0, 4, Color.red, Orientation.down),
                Defender(0, 6, Color.red, Orientation.down),
                Deflector(0, 7, Color.red, Orientation.down),
                Deflector(1, 2, Color.red, Orientation.left),
                Deflector(3, 0, Color.red, Orientation.right),
                Deflector(3, 7, Color.red, Orientation.down),
                Deflector(4, 0, Color.red, Orientation.down),
                Deflector(4, 7, Color.red, Orientation.right),
                Deflector(5, 6, Color.red, Orientation.down),
                Switch(3, 4, Color.red, Orientation.right),
                Switch(3, 5, Color.red, Orientation.down),
                # blue team
                self.blue_laser,
                Queen(7, 4, Color.blue),
                Defender(7, 3, Color.blue, Orientation.up),
                Defender(7, 5, Color.blue, Orientation.up),
                Deflector(7, 2, Color.blue, Orientation.up),
                Deflector(6, 7, Color.blue, Orientation.right),
                Deflector(4, 2, Color.blue, Orientation.up),
                Deflector(4, 9, Color.blue, Orientation.left),
                Deflector(3, 2, Color.blue, Orientation.left),
                Deflector(3, 9, Color.blue, Orientation.up),
                Deflector(2, 3, Color.blue, Orientation.up),
                Switch(4, 4, Color.blue, Orientation.up),
                Switch(4, 5, Color.blue, Orientation.left),
            ]
        )
        self.arrangeTokens()

    def arrangeTokens(self):
        """Place the tokens in the squares."""
        for token in self.tokens:
            row = token.row
            column = token.column
            if self.board.squares[row][column] is not None:
                self.board.squares[row][column].inhabiting_token = token

    def getAllPossibleActions(self, color):
        """Return the possible actions of a player.

        Moves and rotations for each token.
        """
        actions = []
        in_game = [not t.destroyed for t in self.tokens]
        for token in self.tokens[in_game]:
            if token.color == color:
                possible_moves = self.getPossibleMoves(token)
                for move in possible_moves:
                    actions.append(("move", (token, move)))
                possible_rotations = self.getPossibleRotations(token)
                for move in possible_rotations:
                    actions.append(("rotation", (token, move)))
        return actions

    def getPossibleMoves(self, token):
        """Return the squares where a token can move."""

        if token == None:
            return []
        if token.name == "laser":
            return []
        possible_moves = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                row = token.row + i
                column = token.column + j
                if row < 0 or row > 7 or column < 0 or column > 9:
                    continue
                square = self.board.squares[row][column]
                if square.inhabiting_token is None and (
                    square.color == Color.none or square.color == token.color
                ):
                    possible_moves.append(square)
        return possible_moves

    def getPossibleRotations(self, token):
        """Return the possible orientations of a token, excluding the current one."""
        return token.getPossibleRotations()

    def doAction(self, action):
        """Either move or rotate."""
        if action[0] == "move":
            token, square = action[1]
            self.moveToken(token, square)
        else:
            token, orientation = action[1]
            self.rotateToken(token, orientation)

    def moveToken(self, token, end_square, forward=True):
        """Move the token and log the move."""
        start_square = self.board.squares[token.row][token.column]
        token.move(start_square, end_square)

        if forward:
            self.log.append(("move", (token, start_square)))

    def rotateToken(self, token, orientation, forward=True):
        """Rotate the token and log the rotation."""
        start_orientation = token.orientation
        token.changeOrientation(orientation)

        if forward:
            self.log.append(("rotation", (token, start_orientation)))

    def undoLastEvent(self):
        """Retrieve the last move from the event log and undo it."""
        event = self.log.pop()
        if event[0] == "move":
            token, square = event[1]
            self.moveToken(token, square, forward=False)
        if event[0] == "rotation":
            token, orientation = event[1]
            self.rotateToken(token, orientation, forward=False)
        if event[0] == "destruction":
            token = event[1]
            token.destroyed = False
            self.undoLastEvent()

    def is_destroyed(self, token, direction):
        orientation = token.orientation
        name = token.name
        if name == "queen":
            return True
        elif name == "switch":
            return False
        elif name == "defender":
            if (
                direction == Orientation.right
                and orientation == Orientation.left
                or direction == Orientation.left
                and orientation == Orientation.right
                or direction == Orientation.up
                and orientation == Orientation.down
                or direction == Orientation.down
                and orientation == Orientation.up
            ):
                return False
        else:
            if (
                direction == Orientation.right
                and orientation == Orientation.left
                or direction == Orientation.right
                and orientation == Orientation.up
                or direction == Orientation.left
                and orientation == Orientation.right
                or direction == Orientation.left
                and orientation == Orientation.down
                or direction == Orientation.up
                and orientation == Orientation.down
                or direction == Orientation.up
                and orientation == Orientation.left
                or direction == Orientation.down
                and orientation == Orientation.up
                or direction == Orientation.down
                and orientation == Orientation.right
            ):
                return False
        return True

    def reflect_beam(self, token, direction):
        # print("reflect beam from", direction, "by token", token)  # for testing the laser
        col = token.column
        row = token.row
        token_hit = None
        last_position = None
        if direction == Orientation.up:
            while (token_hit is None) and (row > -1):
                token_hit = self.board.squares[row][col].inhabiting_token
                row -= 1
        elif direction == Orientation.down:
            while (token_hit is None) and (row < 8):
                token_hit = self.board.squares[row][col].inhabiting_token
                row += 1
        elif direction == Orientation.left:
            while (token_hit is None) and (col > -1):
                token_hit = self.board.squares[row][col].inhabiting_token
        else:
            while (token_hit is None) and (col < 11):
                token_hit = self.board.squares[row][col].inhabiting_token
        if token_hit is not None:
            self.hitToken(token_hit, direction)
        else:
            self.positions_log.append([row, col])
            self.positions_log.append("out")

    def hitToken(self, token_hit, orientation, verbose=False):
        self.positions_log.append([token_hit.row, token_hit.column])
        if self.is_destroyed(token_hit, orientation) == True:
            token_hit.destroyed = True
            self.board.squares[token_hit.row][token_hit.column].inhabiting_token = None
            self.positions_log.append("destroyed")
            self.log.append(("destruction", token_hit))
            # remove from table
            if verbose:
                print("Hit token", token_hit)
        else:
            self.reflect(token_hit, orientation)

    def reflect(self, token, direction):
        orientation = token.orientation
        name = token.name
        # print("reflect in ", direction, " from ", token)
        if name == "switch":
            if direction == Orientation.right:
                if orientation == Orientation.left or orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.down)
                else:
                    self.reflect_beam(token, Orientation.up)
            elif direction == Orientation.left:
                if orientation == Orientation.left or orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.up)
                else:
                    self.reflect_beam(token, Orientation.down)
            elif direction == Orientation.up:
                if orientation == Orientation.left or orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.left)
                else:
                    self.reflect_beam(token, Orientation.right)
            else:
                if orientation == Orientation.left or orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.right)
                else:
                    self.reflect_beam(token, Orientation.left)
        elif name == "deflector":
            if direction == Orientation.right:
                if orientation == Orientation.left:
                    self.reflect_beam(token, Orientation.down)
                else:  # up
                    self.reflect_beam(token, Orientation.up)
            elif direction == Orientation.left:
                if orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.up)
                else:  # down
                    self.reflect_beam(token, Orientation.down)
            elif direction == Orientation.up:
                if orientation == Orientation.left:
                    self.reflect_beam(token, Orientation.left)
                else:  # down
                    self.reflect_beam(token, Orientation.right)
            else:
                if orientation == Orientation.right:
                    self.reflect_beam(token, Orientation.right)
                else:  # up
                    self.reflect_beam(token, Orientation.left)

    def activate_laser(self, color):
        laser = self.laser_dict[color]
        self.positions_log = []
        row = laser.row
        col = laser.column
        self.positions_log.append([row, col])
        orientation = laser.orientation
        token_hit = None
        last_position = None
        if laser.color == Color.red:
            if orientation == Orientation.down:
                last_position = [7, col]
                for i in range(1, 8):
                    if token_hit == None:
                        token_hit = self.board.squares[row + i][col].inhabiting_token
            else:
                last_position = [row, 9]
                for i in range(1, 10):
                    if token_hit == None:
                        token_hit = self.board.squares[row][col + i].inhabiting_token
        else:
            if orientation == Orientation.up:
                last_position = [0, col]
                for i in range(1, 8):
                    if token_hit == None:
                        token_hit = self.board.squares[row - i][col].inhabiting_token
            else:
                last_position = [row, 0]
                for i in range(1, 10):
                    if token_hit == None:
                        token_hit = self.board.squares[row][col - i].inhabiting_token
        if token_hit != None:
            self.hitToken(token_hit, orientation)
        else:
            self.positions_log.append(last_position)
            self.positions_log.append("out")


class Board:
    """Game board and its evolution."""

    def __init__(self, rows=8, columns=10):
        self.squares = []
        for i in range(rows):
            row = []
            for j in range(columns):
                color = Color.none
                if j == 0 or (j == 8 and (i == 0 or i == 7)):
                    color = Color.red
                elif j == 9 or (j == 1 and (i == 0 or i == 7)):
                    color = Color.blue
                row.append(Square(i, j, color, None))
            self.squares.append(row)

    def unhighlightAllSquares(self):
        for row in self.squares:
            for square in row:
                square.highlighted = False

    # for debugging
    def printCurrentState(self):
        for row in self.squares:
            print(row)


class Square:
    """An elementary part of the board."""

    def __init__(self, row, column, color, inhabiting_token):
        self.row = row
        self.column = column
        self.color = color
        self.inhabiting_token = inhabiting_token
        self.highlighted = False

    def __repr__(self) -> str:
        """Representation of a square: row, column, color, token."""
        return f"({self.row}, {self.column}, {self.color}, {self.inhabiting_token})"


class Token:
    """Parent class for pieces.

    Parameters
    ----------
    name: string

    row, column: integers
        position

    color: Color

    destroyed: boolean
        0 is not hit and 1 is hit
    """

    def __init__(self, row, column, color, destroyed=0):
        self.row = row
        self.column = column
        self.color = color
        self.destroyed = destroyed
        self.name = None

    def __repr__(self) -> str:
        """Representation of a token: color, name."""
        return f"({self.color}, {self.name})"

    def move(self, start_square, end_square):
        """Move the token to the given square.

        Paremeter
        ---------
        square: Square object
            Destination of the token
        """
        self.row = end_square.row
        self.column = end_square.column
        start_square.inhabiting_token = None
        end_square.inhabiting_token = self

    def getPossibleRotations(self):
        """To overwrite."""
        pass


class RotatableToken(Token):
    """Tokens that can rotate.

    Parameters
    ----------
    name: string

    position: Square

    colour: Colour

    hit: boolean
        0 is not hit and 1 is hit

    orientation: int
        n, e, s, w = 0, 1, 2, 3
    """

    def __init__(self, row, column, color, orientation):
        super().__init__(row, column, color)
        self.orientation = orientation

    def changeOrientation(self, orientation):
        """Update the token orientation."""
        self.orientation = Orientation(orientation % 4)

    def rotateClockwise(self):
        """Rotate the token in clockwise direction."""
        self.orientation = Orientation((self.orientation - 1) % 4)

    def rotateAntiClockwise(self):
        """Rotate the token in anti-clockwise direction."""
        self.orientation = Orientation((self.orientation + 1) % 4)

    def after_firing(self, func, *args, **kwargs):
        self.board.after_firing(lambda: func, *args, **kwargs)

    def on_laser_hit(self, orientation, laser):
        self.after_firing(self.remove)

    def remove(self):
        self.board.remove(self)

    def emit(self, laser):
        self.board.fire(laser)


class Queen(Token):
    """Queen class. Square, all of its  4 sides are destroyed by the laser."""

    def __init__(self, row, column, color):
        super().__init__(row, column, color)
        self.name = "queen"
        self.orientation = Orientation.up

    def on_laser_hit(self, orientation, laser):
        self.after_firing(self.board.turn.lose)

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return []

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return []


class Deflector(RotatableToken):
    """Deflector class. Diagonal, one of its 2 sides reflects the laser."""

    def __init__(self, row, column, color, orientation):
        super().__init__(row, column, color, orientation)
        self.name = "deflector"

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return [
            Orientation((self.orientation.value - 1) % 4),
            Orientation((self.orientation.value + 1) % 4),
        ]


class Defender(RotatableToken):
    """Defender class. Square, one of its 4 sides reflects the laser."""

    def __init__(self, row, column, color, orientation):
        super().__init__(row, column, color, orientation)
        self.name = "defender"

    def on_laser_hit(self, direction, laser):
        direction = direction.piece_relative
        if direction is Orientation.DOWN:
            self.after_firing(self.remove)

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return [
            Orientation((self.orientation.value - 1) % 4),
            Orientation((self.orientation.value + 1) % 4),
        ]

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return [
            Orientation((self.orientation.value - 1) % 4),
            Orientation((self.orientation.value + 1) % 4),
        ]


class Switch(RotatableToken):
    """Switch class. Diagonal, both of its sides reflects the laser."""

    def __init__(self, row, column, color, orientation):
        super().__init__(row, column, color, orientation)
        self.name = "switch"

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        return [Orientation(1 - self.orientation.value % 2)]


class Laser(RotatableToken):
    """Laser is always in the same place and can only rotate."""

    def __init__(self, row, column, color, orientation):
        super().__init__(row, column, color, orientation)
        self.name = "laser"

    def getPossibleRotations(self):
        """Return the other possible orientations."""
        dict_orientation = {
            Orientation.right: Orientation.down,
            Orientation.down: Orientation.right,
            Orientation.left: Orientation.up,
            Orientation.up: Orientation.left,
        }
        return [dict_orientation[self.orientation]]

    def rotateClockwise(self):
        """Rotate the token in clockwise direction."""
        self.orientation = self.getPossibleRotations()[0]

    def rotateAntiClockwise(self):
        """Rotate the token in anti-clockwise direction."""
        self.orientation = self.getPossibleRotations()[0]
