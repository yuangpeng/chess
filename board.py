# https://tromp.github.io/go.html
# https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2019_Projects/Dec_12_Demo/Go%20Player/yy852_pg477_Dec:12/index.html
# https://webdocs.cs.ualberta.ca/~hayward/355/gorules.pdf
from __future__ import annotations

import copy
import pickle
import random
from abc import ABC, abstractmethod
from collections import deque
from enum import Enum

from loguru import logger


class Color(Enum):
    EMPTY = "EMPTY"
    BLACK = "BLACK"
    WHITE = "WHITE"


class BaseBoardGame(ABC):
    def __init__(self, size: int, player1_strategy: PlayerStrategy, player2_strategy: PlayerStrategy):
        self.name = ""
        self.size = size
        self.board = [[Color.EMPTY for _ in range(size)] for _ in range(size)]
        self.player1_strategy = player1_strategy
        self.player2_strategy = player2_strategy
        self.round = 0
        self.game_over = False
        self.winner = ""
        self.history: list[Memento] = []  # Use a list of Mementos for the history
        self.replay: list[tuple[int, int] | None] = []
        self.allow_none_move = False

    def cur_player(self) -> Color:
        return Color.BLACK if self.round % 2 == 0 else Color.WHITE

    def opposite_player(self) -> Color:
        return Color.WHITE if self.round % 2 == 0 else Color.BLACK

    @abstractmethod
    def move(self, coord: tuple[int, int] | None = None):
        raise NotImplementedError

    @abstractmethod
    def check_available_moves(self) -> list[tuple[int, int]]:
        raise NotImplementedError

    def cur_player_strategy(self) -> PlayerStrategy:
        return self.player1_strategy if self.cur_player() == Color.BLACK else self.player2_strategy

    def play_round(self):
        move = self.cur_player_strategy().make_move(self)
        self.move(move)

    def surrender(self):
        self.game_over = True
        self.winner = "White" if self.cur_player() == Color.BLACK else "Black"
        logger.info(f"{self.winner} wins.")

    def regret(self):
        if len(self.history) > 0:
            self.restore_from_memento(self.history.pop())
            logger.info("Move undone.")
        else:
            self.restart()

    def restart(self):
        self.__init__(self.size, self.player1_strategy, self.player2_strategy)

    @abstractmethod
    def create_memento(self) -> Memento:
        raise NotImplementedError

    @abstractmethod
    def restore_from_memento(self, memento: Memento):
        raise NotImplementedError

    @abstractmethod
    def save_to_file(self, file_path: str, user1: str, user2: str):
        raise NotImplementedError

    @abstractmethod
    def load_from_file(self, file_path: str, user1: str, user2: str):
        raise NotImplementedError


class Memento:
    def __init__(self, state: dict):
        self.__state = state

    def get_saved_state(self):
        return self.__state


class GoGame(BaseBoardGame):
    # Rule 1: Go is played on a 19x19 square grid of points, by two players called Black and White.
    def __init__(self, size: int, player1_strategy: PlayerStrategy, player2_strategy: PlayerStrategy):
        # Rule 2: Each point on the grid may be colored black, white or empty.
        super().__init__(size, player1_strategy, player2_strategy)
        self.name = "Go Game"
        self.komi = 6.5
        self.ko_point: tuple[int, int] | None = None
        self.last_move_captured = None
        self.abstention = 0
        self.final_score = ""
        self.allow_none_move = True

    def move(self, coord: tuple[int, int] | None = None):
        if coord is not None:
            if coord not in self.check_available_moves():
                return
        if self.game_over:
            return
        if coord is not None:
            # Rule 6: A turn is either a pass or a move that doesn’t repeat an earlier grid coloring (superko).
            if self.ko_point == coord:
                logger.info("Cannot recapture ko immediately.")
                return

            self.history.append(self.create_memento())
            self.replay.append(coord)

            # Rule 5: Starting with an empty grid, the players alternate turns, starting with Black.
            current_color = self.cur_player()
            opposite_color = self.opposite_player()
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
            self.replay.append(None)
            self.abstention += 1
            # Rule 8: The game ends after two consecutive passes.
            if self.abstention == 2:
                # Rule 10: The player with the higher score at the end of the game is the winner. Equal scores result in a tie.
                black_score, white_score = self.score()
                logger.info(f"Game over. Black: {black_score}, White: {white_score}")
                self.game_over = True
                self.winner = f"Black" if black_score > white_score else f"White" if black_score < white_score else f"Tie"
                self.final_score = f"Black: {black_score}, White: {white_score}"

        self.round += 1

    def check_available_moves(self) -> list[tuple[int, int] | None]:
        available_moves = []
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == Color.EMPTY and (x, y) != self.ko_point:
                    available_moves.append((x, y))
        return available_moves

    def create_memento(self) -> Memento:
        # Save the current state in a memento
        state = {
            "name": self.name,
            "size": self.size,
            "board": copy.deepcopy(self.board),
            "round": self.round,
            "game_over": self.game_over,
            "winner": self.winner,
            "final_score": self.final_score,
            # "history": copy.deepcopy(self.history),
            "replay": copy.deepcopy(self.replay),
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
        self.game_over = state["game_over"]
        self.winner = state["winner"]
        self.final_score = state["final_score"]
        # self.history = state["history"]
        self.replay = state["replay"]
        self.komi = state["komi"]
        self.ko_point = state["ko_point"]
        self.last_move_captured = state["last_move_captured"]
        self.abstention = state["abstention"]

    def save_to_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "wb") as file:
            pickle.dump((self.create_memento(), {"user1": user1, "user2": user2}), file)
            logger.info("Game saved to file.")

    def load_from_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "rb") as file:
            memento, account_info = pickle.load(file)
            if account_info["user1"] != user1 or account_info["user2"] != user2:
                logger.warning("The game file does not match the current user.")
            else:
                self.restore_from_memento(memento)
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
        if self.round <= 2:
            return 0, self.komi
        # Rule 9: A player’s score is the number of points of her color, plus the number of empty points that reach only her color.
        black_captures, white_captures = self.remove_dead_stones()
        black_territory, white_territory = self.calculate_territory()

        black_score = len(black_territory) + white_captures
        white_score = len(white_territory) + black_captures + self.komi

        return black_score, white_score


class GomokuGame(BaseBoardGame):
    def __init__(self, size: int, player1_strategy: PlayerStrategy, player2_strategy: PlayerStrategy):
        super().__init__(size, player1_strategy, player2_strategy)
        self.name = "Gomoku Game"

    def move(self, coord: tuple[int, int] | None = None):
        if coord not in self.check_available_moves():
            return
        if self.game_over:
            return
        if coord is None:
            logger.warning("Coord cannot be None.")
            return
        self.history.append(self.create_memento())
        self.replay.append(coord)
        x, y = coord
        self.board[x][y] = self.cur_player()
        if self.is_five(coord):
            self.game_over = True
            self.winner = "Black" if self.cur_player() == Color.BLACK else "White"
            logger.info(f"{self.cur_player().value} wins.")
        self.round += 1

    def check_available_moves(self) -> list[tuple[int, int]]:
        available_moves = []
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == Color.EMPTY:
                    available_moves.append((x, y))
        return available_moves

    def is_five(self, coord: tuple[int, int], return_max_count: bool = False) -> bool:
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        count = 1
        for d in directions:
            count = max(self.count_in_direction(coord, d[0], d[1]) + self.count_in_direction(coord, -d[0], -d[1]) - 1, count)
            if self.count_in_direction(coord, d[0], d[1]) + self.count_in_direction(coord, -d[0], -d[1]) - 1 >= 5:
                if return_max_count:
                    return True, count
                return True
        if return_max_count:
            return False, count
        return False

    def count_in_direction(self, start: tuple[int, int], dx: int, dy: int) -> int:
        count = 0
        x, y = start
        while 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == self.cur_player():
            count += 1
            x += dx
            y += dy
        return count

    def create_memento(self) -> Memento:
        # Save the current state in a memento
        state = {
            "name": self.name,
            "size": self.size,
            "board": copy.deepcopy(self.board),
            "round": self.round,
            "game_over": self.game_over,
            "winner": self.winner,
            # "history": copy.deepcopy(self.history),
            "replay": copy.deepcopy(self.replay),
        }
        return Memento(state)

    def restore_from_memento(self, memento: Memento):
        # Restore the state from the memento
        state = memento.get_saved_state()
        self.name = state["name"]
        self.size = state["size"]
        self.board = state["board"]
        self.round = state["round"]
        self.game_over = state["game_over"]
        self.winner = state["winner"]
        # self.history = state["history"]
        self.replay = state["replay"]

    def save_to_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "wb") as file:
            pickle.dump((self.create_memento(), {"user1": user1, "user2": user2}), file)
            logger.info("Game saved to file.")

    def load_from_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "rb") as file:
            memento, account_info = pickle.load(file)
            if account_info["user1"] != user1 or account_info["user2"] != user2:
                logger.warning("The game file does not match the current user.")
            else:
                self.restore_from_memento(memento)
                logger.info("Game loaded from file.")


class OthelloGame(BaseBoardGame):
    def __init__(self, size: int, player1_strategy: PlayerStrategy, player2_strategy: PlayerStrategy):
        logger.warning(f"only support size 8 for now, {size} will be ignored")
        super().__init__(8, player1_strategy, player2_strategy)
        self.name = "Othello Game"
        # Initialize the board with the starting positions
        mid = self.size // 2
        self.board[mid - 1][mid - 1] = self.board[mid][mid] = Color.WHITE
        self.board[mid - 1][mid] = self.board[mid][mid - 1] = Color.BLACK

    def move(self, coord: tuple[int, int] | None):
        if self.game_over:
            return
        # if coord is None:
        #     logger.warning("You cannot pass proactively.")
        #     return
        available_moves = self.check_available_moves()
        if len(available_moves) == 0:
            self.history.append(self.create_memento())
            self.replay.append(None)
            self.round += 1
        else:
            if coord in available_moves:
                self.history.append(self.create_memento())
                self.replay.append(coord)
                self.board[coord[0]][coord[1]] = self.cur_player()
                self.clamp(coord, clear=True)
                if self.check_game_over():
                    self.game_over = True
                    self.winner = self.get_winner()
                self.round += 1
            else:
                logger.warning("Invalid move.")

    def get_winner(self):
        black_score = 0
        white_score = 0
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == Color.BLACK:
                    black_score += 1
                elif self.board[x][y] == Color.WHITE:
                    white_score += 1
        if black_score > white_score:
            return "Black"
        elif black_score < white_score:
            return "White"

    def check_game_over(self) -> bool:
        # Implement the logic to check if the game is over
        cur_available_moves = self.check_available_moves()
        self.round += 1
        next_available_moves = self.check_available_moves()
        self.round -= 1
        return len(cur_available_moves) == 0 and len(next_available_moves) == 0

    def check_available_moves(self) -> list[tuple[int, int]]:
        available_moves = []
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == Color.EMPTY and self.clamp((x, y), clear=False):
                    available_moves.append((x, y))
        return available_moves

    def clamp(self, coord: tuple[int, int], clear: bool = False, return_count: bool = False) -> bool | tuple[bool, int]:
        directions = [(1, 0), (0, 1), (1, 1), (1, -1), (-1, 0), (0, -1), (-1, -1), (-1, 1)]
        if return_count:
            return any([self.clamp_direction(coord, d[0], d[1], clear=clear, return_count=return_count)[0] for d in directions]), sum(
                [self.clamp_direction(coord, d[0], d[1], clear=clear, return_count=return_count)[1] for d in directions]
            )
        return any([self.clamp_direction(coord, d[0], d[1], clear=clear) for d in directions])

    def clamp_direction(self, coord: tuple[int, int], dx: int, dy: int, clear: bool = False, return_count: bool = False) -> bool | tuple[bool, int]:
        x, y = coord
        x += dx
        y += dy
        opposite_list = []
        while 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == self.opposite_player():
            opposite_list.append((x, y))
            x += dx
            y += dy
        if 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == self.cur_player():
            if clear:
                for opposite in opposite_list:
                    self.board[opposite[0]][opposite[1]] = self.cur_player()
            if return_count:
                return len(opposite_list) > 0, len(opposite_list)
            return len(opposite_list) > 0
        if return_count:
            return False, 0
        return False

    def create_memento(self) -> Memento:
        # Save the current state in a memento
        state = {
            "name": self.name,
            "size": self.size,
            "board": copy.deepcopy(self.board),
            "round": self.round,
            "game_over": self.game_over,
            "winner": self.winner,
            # "history": copy.deepcopy(self.history),
            "replay": copy.deepcopy(self.replay),
        }
        return Memento(state)

    def restore_from_memento(self, memento: Memento):
        # Restore the state from the memento
        state = memento.get_saved_state()
        self.name = state["name"]
        self.size = state["size"]
        self.board = state["board"]
        self.round = state["round"]
        self.game_over = state["game_over"]
        self.winner = state["winner"]
        # self.history = state["history"]
        self.replay = state["replay"]

    def save_to_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "wb") as file:
            pickle.dump((self.create_memento(), {"user1": user1, "user2": user2}), file)
            logger.info("Game saved to file.")

    def load_from_file(self, file_path: str, user1: str, user2: str):
        with open(file_path, "rb") as file:
            memento, account_info = pickle.load(file)
            if account_info["user1"] != user1 or account_info["user2"] != user2:
                logger.warning("The game file does not match the current user.")
            else:
                self.restore_from_memento(memento)
                logger.info("Game loaded from file.")


class PlayerStrategy(ABC):
    role = None
    color = Color.BLACK

    def __init__(self, color):
        self.color = color

    @abstractmethod
    def make_move(self, game: BaseBoardGame) -> tuple[int, int] | None:
        pass


class HumanPlayerStrategy(PlayerStrategy):
    role = "Human"
    move = None

    def get_move(self, move: tuple[int, int] | None):
        self.move = move

    def make_move(self, game: BaseBoardGame) -> tuple[int, int] | None:
        return self.move


class Level1AIPlayerStrategy(PlayerStrategy):
    role = "Level1 AI"

    # Random Move
    def make_move(self, game: BaseBoardGame) -> tuple[int, int] | None:
        available_moves = game.check_available_moves()
        if game.allow_none_move:
            available_moves.append(None)
        if len(available_moves) == 0:
            return None
        return random.choice(available_moves)


class Level2AIPlayerStrategy(PlayerStrategy):
    role = "Level2 AI"

    # Simple Rules
    def make_move(self, game: BaseBoardGame) -> tuple[int, int] | None:
        if game.name == "Gomoku Game":
            available_moves = game.check_available_moves()
            best_move = random.choice(available_moves)
            best_score = -1
            for x, y in available_moves:
                game.board[x][y] = self.color
                _, score = game.is_five((x, y), return_max_count=True)
                if score > best_score:
                    best_move = (x, y)
                    best_score = score
                game.board[x][y] = Color.EMPTY
            return best_move
        elif game.name == "Othello Game":
            available_moves = game.check_available_moves()
            if len(available_moves) == 0:
                return None
            corner_points = [(0, 0), (0, game.size - 1), (game.size - 1, 0), (game.size - 1, game.size - 1)]
            edge_points = (
                [(0, y) for y in range(game.size)]
                + [(game.size - 1, y) for y in range(game.size)]
                + [(x, 0) for x in range(game.size)]
                + [(x, game.size - 1) for x in range(game.size)]
            )
            for x, y in available_moves:
                if (x, y) in corner_points:
                    return x, y
            best_move = random.choice(available_moves)
            best_score = -99999999
            for x, y in available_moves:
                board_back = copy.deepcopy(game.board)
                game.board[x][y] = self.color
                game.round += 1
                _, score = game.clamp((x, y), clear=True, return_count=True)

                opposite_available_moves = game.check_available_moves()
                best_opposite_score = -99999999
                for i, j in opposite_available_moves:
                    game.board[i][j] = Color.WHITE if self.color == Color.BLACK else Color.BLACK
                    game.round += 1
                    _, opposite_score = game.clamp((i, j), clear=False, return_count=True)
                    if opposite_score > best_opposite_score:
                        best_opposite_score = opposite_score
                    game.board[i][j] = Color.EMPTY
                    game.round -= 1

                if (x, y) in edge_points:
                    score += 0.5
                score -= best_opposite_score
                if score > best_score:
                    best_move = (x, y)
                    best_score = score
                game.round -= 1
                game.board = board_back
            logger.info(f"Best score: {best_score}, best move: {best_move}")
            return best_move


class Level3AIPlayerStrategy(PlayerStrategy):
    role = "Level3 AI"

    def make_move(self, game: BaseBoardGame) -> tuple[int, int] | None:
        available_moves = game.check_available_moves()
        if game.allow_none_move:
            available_moves.append(None)
        if len(available_moves) == 0:
            return None
        return random.choice(available_moves)
