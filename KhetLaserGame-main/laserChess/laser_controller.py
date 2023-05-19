"""
The controller connects the model and the view.

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

import laser_model as model


class BaseController:
    """Traditionnal functionalities of a controller."""

    def __init__(self):
        self.clients = list()
        self.message = ""

    def add_client(self, client):
        """Add client to the list of elements the controller will manage."""
        self.clients.append(client)

    def refresh_all(self, message):
        """Update all known elements."""
        self.message = message
        for client in self.clients:
            client.refresh()


class GameController(BaseController):
    """Parameters and methods to manage the sequence of events."""

    def __init__(self):
        super().__init__()

    def start(self, red_player_type, blue_player_type):
        """Initialise the game."""
        print("Starting new game...")
        print("Red player: " + red_player_type)
        print("Blue player: " + blue_player_type)
        self.game = model.Game()
        # Red player
        self.red_player = model.Player(model.Color.red, "Human")
        if red_player_type == "AI":
            self.red_player = model.AI(self.game, color=model.Color.red, depth_limit=1)
        # Blue player
        self.blue_player = model.Player(model.Color.blue, "Human")
        if blue_player_type == "AI":
            self.blue_player = model.AI(
                self.game, color=model.Color.blue, depth_limit=1
            )
        self.selected_token = None
        self.refresh_all("")

    def squareSelected(self, row, column):
        if self.game.board.squares[row][column].highlighted:
            self.game.moveToken(
                self.selected_token, self.game.board.squares[row][column]
            )
            self.finishTurn()
            self.game.board.unhighlightAllSquares()
            self.selected_token = None
        else:
            self.game.board.unhighlightAllSquares()
            self.selected_token = self.game.board.squares[row][column].inhabiting_token
            if self.selected_token == None:
                return
            elif self.selected_token.color == self.getCurrentPlayerColor():
                self.selected_token = None
            else:
                for possible_move in self.game.getPossibleMoves(self.selected_token):
                    self.game.board.squares[possible_move.row][
                        possible_move.column
                    ].highlighted = True
        self.refresh_all("")

    def getCurrentPlayerColor(self):
        if self.game.turn % 2 == 0:
            return model.Color.red
        else:
            return model.Color.blue

    def rotateSelectedTokenClockwise(self):
        self.selected_token.rotateClockwise()
        self.game.board.unhighlightAllSquares()
        self.selected_token = None
        self.finishTurn()
        self.refresh_all("")

    def rotateSelectedTokenAntiClockwise(self):
        self.selected_token.rotateAntiClockwise()
        self.game.board.unhighlightAllSquares()
        self.selected_token = None
        self.finishTurn()
        self.refresh_all("")

    def finishTurn(self):
        print("Turn finished")
        color = model.Color.blue if self.game.turn % 2 else model.Color.red
        self.game.activate_laser(color)
        self.game.turn += 1
        self.refresh_all("")

    def test_AI(self):
        # try:
        print("Thinking")
        action = (
            self.blue_player.minimax()
            if self.game.turn % 2
            else self.red_player.minimax()
        )
        print("move decided", action)
        self.game.doAction(action)
        self.finishTurn()
        self.refresh_all("")

    # except Exception:
    #     print("The game probably did not start or the current player is not an AI")
