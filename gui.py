from __future__ import annotations

import sys

import pygame

from board import Color, BaseBoardGame, GoGame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BACKGROUND = (175, 135, 0)


class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)
        font = pygame.font.SysFont(None, 24)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()


class BoardGameGUI:
    def __init__(self, game: BaseBoardGame, grid_size: int = 40):
        self.game = game

        # Initialize pygame, and create the screen
        pygame.init()
        self.grid_size = grid_size
        self.windows_size = self.grid_size * (self.game.size + 1)
        self.screen = pygame.display.set_mode((self.windows_size, self.windows_size))
        pygame.display.set_caption(f"{self.game.name}")
        self.stone_radius = self.grid_size // 2 - 2

    def draw_current_player(self):
        font = pygame.font.SysFont(None, 36)
        if self.game.cur_player() == Color.BLACK:
            text = font.render("Current Player: Black", True, BLACK)
        else:
            text = font.render("Current Player: White", True, WHITE)
        self.screen.blit(text, (10, 10))

    def draw_board(self):
        self.screen.fill(BACKGROUND)
        for row in range(self.game.size):
            for col in range(self.game.size):
                pygame.draw.rect(
                    self.screen,
                    BLACK,
                    (self.grid_size + col * self.grid_size - 1, self.grid_size + row * self.grid_size - 1, 2, 2),
                )
                if self.game.board[row][col] in (Color.BLACK, Color.WHITE):
                    if self.game.board[row][col] == Color.BLACK:
                        draw_color = BLACK
                    else:
                        draw_color = WHITE
                    pygame.draw.circle(
                        self.screen,
                        draw_color,
                        (self.grid_size + col * self.grid_size, self.grid_size + row * self.grid_size),
                        self.stone_radius,
                    )

    def create_buttons(self):
        self.buttons = [
            Button(10, self.windows_size - 70, 100, 50, "Undo", self.undo_move),
            Button(120, self.windows_size - 70, 100, 50, "Restart", self.restart_game),
            Button(230, self.windows_size - 70, 100, 50, "Pass", self.pass_turn),
            Button(340, self.windows_size - 70, 100, 50, "Save", lambda: self.save_game_state("game_state.txt")),
            Button(450, self.windows_size - 70, 100, 50, "Load", lambda: self.load_game_state("game_state.txt")),
        ]

    def draw_buttons(self):
        for button in self.buttons:
            button.draw(self.screen)

    def undo_move(self):
        self.game.regret()

    def restart_game(self):
        self.game.restart()

    def pass_turn(self):
        self.game.move(None)

    def save_game_state(self, filename):
        self.game.save_to_file(filename)

    def load_game_state(self, filename):
        self.game.load_from_file(filename)

    def handle_mouse_click(self, pos: tuple(float, float)):
        x, y = pos
        row = round((y - self.grid_size) / self.grid_size)
        col = round((x - self.grid_size) / self.grid_size)

        if 0 <= row < self.game.size and 0 <= col < self.game.size and self.game.board[row][col] == Color.EMPTY:
            self.game.move((row, col))

    def start_game(self):
        self.create_buttons()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for button in self.buttons:
                            button.handle_event(event)
                        pos = pygame.mouse.get_pos()
                        if pos[1] < self.windows_size - 80:
                            self.handle_mouse_click(pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:
                        self.undo_move()
                    elif event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_p:
                        self.pass_turn()
                    elif event.key == pygame.K_s:
                        self.save_game_state("game_state.txt")
                    elif event.key == pygame.K_l:
                        self.load_game_state("game_state.txt")
                    elif event.key == pygame.K_q:
                        running = False
                self.draw_board()
                self.draw_current_player()
                self.draw_buttons()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # 初始化游戏和GUI
    go_game = GoGame(19)
    gui = BoardGameGUI(go_game)
    gui.start_game()
