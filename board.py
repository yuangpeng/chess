# https://tromp.github.io/go.html
# https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2019_Projects/Dec_12_Demo/Go%20Player/yy852_pg477_Dec:12/index.html

# Go.py
from itertools import product

from enum import Enum


class Color(Enum):
    EMPTY = "EMPTY"
    BLACK = "BLACK"
    WHITE = "WHITE"


class GoGame:
    def __init__(self, size: int):
        self.size = size
        self.board = [[Color.EMPTY for _ in range(size)] for _ in range(size)]
        self.__turns = 0

    def move(self, coord: tuple(int, int) | None = None):
        if coord is not None:
            x, y = coord
            if self.turns % 2 == 0:
                self.board[x][y] = Color.BLACK
            else:
                self.board[x][y] = Color.WHITE
            opponent = [nbr for nbr in self.neighbors(coord) if self.board[nbr[0]][nbr[1]] != self.board[x][y]]
            self.clear(opponent)
            self.clear(coord)

        self.__turns += 1

    def neighbors(self, coord: tuple(int, int)) -> list(tuple(int, int)):
        x, y = coord
        return [(x, ny) for ny in (y - 1, y + 1) if 1 <= ny <= self.size] + [(nx, y) for nx in (x - 1, x + 1) if 1 <= nx <= self.size]

    def clear(self, points: tuple(int, int) | list(tuple(int, int))):
        captured = set()
        for pt in points:
            str_points = self.string(pt)
            if not self.liberties(str_points):
                captured.update(str_points)
        for cap in captured:
            self.board[cap[0]][cap[1]] = Color.EMPTY

    def string(self, coord: tuple(int, int)) -> list(tuple(int, int)):
        def expand(curr: list(tuple(int, int)), prev: list(tuple(int, int))):
            next_points = set(nbr for p in curr for nbr in self.neighbors(p) if self.board[nbr[0]][nbr[1]] == self.board[coord[0]][coord[1]]) - set(prev)
            return expand([next_points], [curr]) if next_points else [curr, prev]

        return expand([coord], [])[0]

    def liberties(self, group: list(tuple(int, int))) -> bool:
        empty = [nbr for p in group for nbr in self.neighbors(p) if self.board[nbr[0]][nbr[1]] == Color.EMPTY]
        return len(empty) > 0

    @property
    def turns(self):
        return self.__turns


# Article 1a: Go is played on a 19x19 square grid of points
size = 19
coords = list(range(1, size + 1))
points = [(x, y) for x in coords for y in coords]


# Article 1b: by two players called Black and White
class Player:
    BLACK = "Black"
    WHITE = "White"


# Article 2: Each point on the grid may be colored black, white or empty.
# class Color:
#     EMPTY = "Empty"
#     STONE = {Player.BLACK: "Black", Player.WHITE: "White"}


# Article 3b: if there is a path of (vertically or horizontally) adjacent points of P's color from P
def neighbours(point):
    x, y = point
    return [(x, ny) for ny in (y - 1, y + 1) if 1 <= ny <= size] + [(nx, y) for nx in (x - 1, x + 1) if 1 <= nx <= size]


def string(pos, point):
    def expand(curr, prev):
        next_points = set(nbr for p in curr for nbr in neighbours(p) if pos[nbr] == pos[point]) - set(prev)
        return [next_points, curr] if next_points else [curr, prev]

    return expand([point], [])


# Article 4: Clearing a color is the process of emptying all points of that color
def clear(pos, points):
    def new_pos(pt):
        return Color.EMPTY if pt in captured else pos[pt]

    captured = set()
    for pt in points:
        str_points = string(pos, pt)
        if not liberties(pos, str_points[0]):
            captured.update(str_points[0])
    return {pt: new_pos(pt) for pt in pos}


# Article 4b: that don't reach empty.
def liberties(pos, group):
    empty = [nbr for p in group for nbr in neighbours(p) if pos[nbr] == Color.EMPTY]
    return len(empty) > 0


# Article 5a: Starting with an empty grid
empty_pos = {pt: Color.EMPTY for pt in points}


# Article 5b: the players alternate turns, starting with Black.
def results(turns):
    past_positions = [empty_pos]
    for turn in turns:
        past_positions.append(play(turn, past_positions[-1]))
    return past_positions


# Article 6a: A turn is either a pass; or a move
class Turn:
    def __init__(self, move=None):
        self.move = move


# Article 6b: that doesn't repeat an earlier grid coloring.
class GoError(Exception):
    pass


def testko(pos, past):
    # if pos in past:
    #     raise GoError("Superko violation")
    return pos


# Article 7: A move consists of coloring an empty point one's own color; then clearing the opponent color, and then clearing one's own color.
def move(player, point, pos):
    pos1 = pos.copy()
    pos1[point] = Color.STONE[player]
    opponent = [nbr for nbr in neighbours(point) if pos1[nbr] == Color.STONE[player]]
    pos2 = clear(pos1, opponent)
    pos3 = clear(pos2, [point])
    return pos3


def play(turn, pos):
    if isinstance(turn, Turn):
        if turn.move:
            point = turn.move
            player = (
                Player.BLACK
                if sum(1 for p in pos.values() if p == Color.STONE[Player.BLACK]) <= sum(1 for p in pos.values() if p == Color.STONE[Player.WHITE])
                else Player.WHITE
            )
            if pos[point] != Color.EMPTY:
                raise GoError("Occupied")
            new_pos = move(player, point, pos)
            return testko(new_pos, pos)
        else:
            return pos  # Pass
    else:
        raise ValueError("Invalid turn")


# Article 8: The game ends after two consecutive passes.
def gameover(past_positions):
    if past_positions[-1] == past_positions[-2]:
        bscore, wscore = score(past_positions[-1], Player.BLACK), score(past_positions[-1], Player.WHITE)
        return f"\nGame Over. Black: {bscore} White: {wscore}. {winner(bscore, wscore)}\n"
    return ""


# Article 9: A player's score is the number of points of her color, plus the number of empty points that reach only her color.
def score(pos, player):
    return sum(1 for pt, owner in pos.items() if owner == Color.STONE[player] or (owner == Color.EMPTY and reachable_only_by(pos, pt, player)))


def reachable_only_by(pos, pt, player):
    return all(pos[nbr] in (Color.STONE[player], Color.EMPTY) for nbr in neighbours(pt))


# Article 10: The player with the higher score at the end of the game is the winner. Equal scores result in a tie.
def winner(bscore, wscore):
    if bscore > wscore:
        return "Black wins."
    elif bscore < wscore:
        return "White wins."
    else:
        return "It's a tie."


# Show stuff
def show_pos(pos):
    return "\n".join(
        " ".join(Color.EMPTY if pos[(x, y)] == Color.EMPTY else "@" if pos[(x, y)] == Color.STONE[Player.BLACK] else "O" for x in coords)
        for y in reversed(coords)
    )


def show_game(game):
    import ipdb

    ipdb.set_trace()
    past_positions = results(game)
    print(show_pos(empty_pos))
    for pos in past_positions:
        print(show_pos(pos))


# Example game
game = [Turn((2, 1)), Turn((2, 3)), Turn((2, 2)), Turn((3, 2)), Turn((1, 2)), Turn(), Turn()]

if __name__ == "__main__":
    show_game(game)
