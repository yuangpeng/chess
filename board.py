# https://tromp.github.io/go.html
# https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2019_Projects/Dec_12_Demo/Go%20Player/yy852_pg477_Dec:12/index.html
# https://webdocs.cs.ualberta.ca/~hayward/355/gorules.pdf
from __future__ import annotations

from collections import deque
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger
import pickle
import copy
from collections import deque


class Color(Enum):
    EMPTY = "EMPTY"
    BLACK = "BLACK"
    WHITE = "WHITE"


class BaseBoardGame(ABC):
    def __init__(self, size: int):
        self.name = ""
        self.size = size
        self.board = [[Color.EMPTY for _ in range(size)] for _ in range(size)]
        self.round = 0
        self.history: list[Memento] = []  # Use a list of Mementos for the history

    def cur_player(self) -> Color:
        return Color.BLACK if self.round % 2 == 0 else Color.WHITE

    @abstractmethod
    def move(self, coord: tuple[int, int] | None = None):
        raise NotImplementedError

    @abstractmethod
    def regret(self):
        raise NotImplementedError

    @abstractmethod
    def restart(self):
        raise NotImplementedError

    @abstractmethod
    def create_memento(self) -> Memento:
        raise NotImplementedError

    @abstractmethod
    def restore_from_memento(self, memento: Memento):
        raise NotImplementedError

    @abstractmethod
    def save_to_file(self, file_path: str):
        raise NotImplementedError

    @abstractmethod
    def load_from_file(self, file_path: str):
        raise NotImplementedError


class Memento:
    def __init__(self, state: dict):
        self.__state = state

    def get_saved_state(self):
        return self.__state


class GoGame(BaseBoardGame):
    # Rule 1: Go is played on a 19x19 square grid of points, by two players called Black and White.
    def __init__(self, size: int):
        # Rule 2: Each point on the grid may be colored black, white or empty.
        super().__init__(size)
        self.name = "Go Game"
        self.komi = 6.5
        self.ko_point: tuple[int, int] | None = None
        self.last_move_captured = None
        self.abstention = 0

    def move(self, coord: tuple[int, int] | None = None):
        if coord is not None:
            # Rule 6: A turn is either a pass or a move that doesn’t repeat an earlier grid coloring (superko).
            if self.ko_point == coord:
                logger.info("Cannot recapture ko immediately.")
                return

            self.history.append(self.create_memento())

            # Rule 5: Starting with an empty grid, the players alternate turns, starting with Black.
            current_color = self.cur_player()
            opposite_color = Color.WHITE if current_color == Color.BLACK else Color.BLACK
            x, y = coord
            # Rule 7: A move consists of coloring an empty point one’s own color; then clearing the opponent color, and then clearing one’s own color.
            self.board[x][y] = current_color
            opponent = [nbr for nbr in self.neighbors(coord) if self.board[nbr[0]][nbr[1]] == opposite_color]
            captured = self.clear(opponent)

            # set ko point
            if len(captured) == 1:
                self.ko_point = captured.pop()
            else:
                self.ko_point = None

            self.clear(coord)
        else:  # pass
            self.history.append(self.create_memento())
            self.abstention += 1
            # Rule 8: The game ends after two consecutive passes.
            if self.abstention == 2:
                # Rule 10: The player with the higher score at the end of the game is the winner. Equal scores result in a tie.
                black_score, white_score = self.score()
                logger.info("Game over.")
                logger.info(f"Black: {black_score} White: {white_score}.")

        self.round += 1

    def regret(self):
        if len(self.history) > 0:
            self.restore_from_memento(self.history.pop())
            logger.info("Move undone.")
        else:
            self.restart()

    def restart(self):
        self.__init__(self.size)

    def create_memento(self) -> Memento:
        # Save the current state in a memento
        state = {
            "name": self.name,
            "size": self.size,
            "board": copy.deepcopy(self.board),
            "round": self.round,
            # "history": copy.deepcopy(self.history),
            "komi": self.komi,
            "ko_point": self.ko_point,
            "last_move_captured": self.last_move_captured,
            "abstention": self.abstention,
        }
        return Memento(state)

    def restore_from_memento(self, memento: Memento):
        # Restore the state from the memento
        state = memento.get_saved_state()
        self.name = state["name"]
        self.size = state["size"]
        self.board = state["board"]
        self.round = state["round"]
        # self.history = state["history"]
        self.komi = state["komi"]
        self.ko_point = state["ko_point"]
        self.last_move_captured = state["last_move_captured"]
        self.abstention = state["abstention"]

    def save_to_file(self, file_path: str):
        with open(file_path, "wb") as file:
            pickle.dump(self.create_memento(), file)
            logger.info("Game saved to file.")

    def load_from_file(self, file_path: str):
        with open(file_path, "rb") as file:
            self.restore_from_memento(pickle.load(file))
            logger.info("Game loaded from file.")

    def neighbors(self, coord: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = coord
        return [(x, ny) for ny in (y - 1, y + 1) if 0 <= ny < self.size] + [(nx, y) for nx in (x - 1, x + 1) if 0 <= nx < self.size]

    # Rule 4: Clearing a color is the process of emptying all points of that color that don’t reach empty.
    def clear(self, points: tuple[int, int] | list[tuple[int, int]]) -> set[tuple[int, int]]:
        if isinstance(points, tuple):
            points = [points]
        captured = set()
        for pt in points:
            str_points = self.string(pt)
            if not self.liberties(str_points):
                captured.update(str_points)
        for cap in captured:
            self.board[cap[0]][cap[1]] = Color.EMPTY
        return captured

    # Rule 3: A point P, not colored C, is said to reach C if there is a path of (vertically or horizontally) adjacent points of P’s color from P to a point of color C.
    def string(self, coord: tuple[int, int]) -> list[tuple[int, int]]:
        visited = set()
        visited.add(coord)

        queue = deque([coord])

        while queue:
            for nbr in self.neighbors(queue.popleft()):
                if self.board[nbr[0]][nbr[1]] == self.board[coord[0]][coord[1]] and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

        return visited

    def liberties(self, group: list[tuple[int, int]]) -> bool:
        empty = [nbr for p in group for nbr in self.neighbors(p) if self.board[nbr[0]][nbr[1]] == Color.EMPTY]
        return len(empty) > 0

    def calculate_territory(self) -> tuple(set[tuple[int, int]], set[tuple[int, int]]):
        black_territory = set()
        white_territory = set()
        neutral_territory = set()
        visited = set()

        for x in range(self.size):
            for y in range(self.size):
                if (x, y) in visited or self.board[x][y] != Color.EMPTY:
                    continue

                territory, borders = self.flood_fill((x, y))
                visited.update(territory)

                # Determine the territory's ownership by its borders
                if all(self.board[x][y] == Color.BLACK for x, y in borders):
                    black_territory.update(territory)
                elif all(self.board[x][y] == Color.WHITE for x, y in borders):
                    white_territory.update(territory)
                else:
                    neutral_territory.update(territory)

        return black_territory, white_territory

    def remove_dead_stones(self) -> tuple[int, int]:
        return 0, 0

    def flood_fill(self, start: tuple[int, int]):
        queue = deque([start])
        territory = set([start])
        borders = set()

        while queue:
            x, y = queue.popleft()
            for nx, ny in self.neighbors((x, y)):
                if (nx, ny) in territory:
                    continue

                if self.board[nx][ny] == Color.EMPTY:
                    queue.append((nx, ny))
                    territory.add((nx, ny))
                else:
                    borders.add((nx, ny))

        return territory, borders

    def score(self):
        # Rule 9: A player’s score is the number of points of her color, plus the number of empty points that reach only her color.
        black_captures, white_captures = self.remove_dead_stones()
        black_territory, white_territory = self.calculate_territory()

        black_score = len(black_territory) + white_captures
        white_score = len(white_territory) + black_captures + self.komi

        return black_score, white_score
