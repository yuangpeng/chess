from __future__ import annotations
import tkinter as tk
from collections import deque


class Color:
    EMPTY = 0
    BLACK = 1
    WHITE = 2


# 你的 GoGame 类代码 ...
class GoGame:
    def __init__(self, size: int):
        self.size = size
        self.board = [[Color.EMPTY for _ in range(size)] for _ in range(size)]
        self.__turns = 0

    def move(self, coord: tuple[int, int] | None = None):
        if coord is not None:
            x, y = coord
            if self.turns % 2 == 0:
                self.board[x][y] = Color.BLACK
            else:
                self.board[x][y] = Color.WHITE
            opponent = [nbr for nbr in self.neighbors(coord) if self.board[nbr[0]][nbr[1]] != self.board[x][y] and self.board[nbr[0]][nbr[1]] != Color.EMPTY]
            self.clear(opponent)
            self.clear(coord)

        self.__turns += 1

    def neighbors(self, coord: tuple[int, int]) -> list(tuple[int, int]):
        x, y = coord
        return [(x, ny) for ny in (y - 1, y + 1) if 1 <= ny <= self.size] + [(nx, y) for nx in (x - 1, x + 1) if 1 <= nx <= self.size]

    def clear(self, points: tuple[int, int] | list[tuple[int, int]]):
        if isinstance(points, tuple):
            points = [points]
        captured = set()
        for pt in points:
            str_points = self.string(pt)
            if not self.liberties(str_points):
                captured.update(str_points)
        for cap in captured:
            self.board[cap[0]][cap[1]] = Color.EMPTY

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

    @property
    def turns(self):
        return self.__turns


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
