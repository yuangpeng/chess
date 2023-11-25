# https://tromp.github.io/go.html
# https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2019_Projects/Dec_12_Demo/Go%20Player/yy852_pg477_Dec:12/index.html
# https://webdocs.cs.ualberta.ca/~hayward/355/gorules.pdf
from __future__ import annotations

from collections import deque
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger


class Color(Enum):
    EMPTY = "EMPTY"
    BLACK = "BLACK"
    WHITE = "WHITE"


class BaseBoard(ABC):
    def __init__(self, size: int):
        self.size = size
        self.board = [[Color.EMPTY for _ in range(size)] for _ in range(size)]
        self.round = 0

    @abstractmethod
    def move(self, coord: tuple(int, int) | None = None):
        raise NotImplementedError


class GoGame(BaseBoard):
    # Rule 1: Go is played on a 19x19 square grid of points, by two players called Black and White.
    def __init__(self, size: int):
        # Rule 2: Each point on the grid may be colored black, white or empty.
        super().__init__(size)
        self.komi = 6.5
        self.ko_point: tuple(int, int) | None = None
        self.last_move_captured = None
        self.abstention = 0

    def move(self, coord: tuple(int, int) | None = None):
        if coord is not None:
            # Rule 6: A turn is either a pass or a move that doesn’t repeat an earlier grid coloring (superko).
            if self.ko_point == coord:
                logger.info("Cannot recapture ko immediately.")
                return

            # Rule 5: Starting with an empty grid, the players alternate turns, starting with Black.
            current_color = Color.BLACK if self.round % 2 == 0 else Color.WHITE
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
        else:
            self.abstention += 1
            # Rule 8: The game ends after two consecutive passes.
            if self.abstention == 2:
                # Rule 10: The player with the higher score at the end of the game is the winner. Equal scores result in a tie.
                black_score, white_score = self.score()
                logger.info("Game over.")
                logger.info(f"Black: {black_score} White: {white_score}.")

        self.round += 1

    def neighbors(self, coord: tuple(int, int)) -> list(tuple(int, int)):
        x, y = coord
        return [(x, ny) for ny in (y - 1, y + 1) if 1 <= ny <= self.size] + [(nx, y) for nx in (x - 1, x + 1) if 1 <= nx <= self.size]

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
    def string(self, coord: tuple[int, int]) -> list(tuple[int, int]):
        visited = set()
        visited.add(coord)

        queue = deque([coord])

        while queue:
            for nbr in self.neighbors(queue.popleft()):
                if self.board[nbr[0]][nbr[1]] == self.board[coord[0]][coord[1]] and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

        return visited

    def liberties(self, group: list(tuple[int, int])) -> bool:
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

    def remove_dead_stones(self) -> tuple(int, int):
        return 0, 0

    def flood_fill(self, start: tuple(int, int)):
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


import pygame
import sys

# Constants
BOARD_SIZE = 19
GRID_SIZE = 40
WINDOW_SIZE = GRID_SIZE * (BOARD_SIZE + 1)
STONE_RADIUS = GRID_SIZE // 2 - 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BACKGROUND = (175, 135, 0)
go_game = GoGame(BOARD_SIZE)

# Initialize pygame
pygame.init()

# Create the screen
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Go Game")

# Initialize the board
# board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
# current_color = BLACK


def draw_board():
    screen.fill(BACKGROUND)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            pygame.draw.rect(screen, BLACK, (GRID_SIZE + col * GRID_SIZE - 1, GRID_SIZE + row * GRID_SIZE - 1, 2, 2))
            if go_game.board[row][col] in (Color.BLACK, Color.WHITE):
                if go_game.board[row][col] == Color.BLACK:
                    draw_color = BLACK
                else:
                    draw_color = WHITE
                pygame.draw.circle(screen, draw_color, (GRID_SIZE + col * GRID_SIZE, GRID_SIZE + row * GRID_SIZE), STONE_RADIUS)


def handle_mouse_click(pos):
    # global current_color
    x, y = pos
    row = round((y - GRID_SIZE) / GRID_SIZE)
    col = round((x - GRID_SIZE) / GRID_SIZE)

    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and go_game.board[row][col] == Color.EMPTY:
        go_game.move((row, col))
        draw_board()  # Redraw the board to show the updated state


# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_click(pygame.mouse.get_pos())
            draw_board()  # Redraw the board after every click

    pygame.display.flip()


pygame.quit()
sys.exit()
