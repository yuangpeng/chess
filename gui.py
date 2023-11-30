from __future__ import annotations

import sys

import pygame

from board import BaseBoardGame, Color, GoGame, GomokuGame, OthelloGame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BACKGROUND = (175, 135, 0)


class Button:
    def __init__(self, x, y, width, height, ratio, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.ratio = ratio
        self.text = text
        self.callback = callback

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event) -> bool:
        is_handle = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                is_handle = True
        return is_handle


class BoardGameGUI:
    def __init__(self, grid_size: int = 40, sidebar_width: int = 300):
        # default go game with 19-way
        self.game_list: list[BaseBoardGame] = [GoGame, GomokuGame, OthelloGame]
        self.cur_game_type = self.game_list[0]
        self.size = 19
        self.game: BaseBoardGame = self.cur_game_type(self.size)

        self.ratio = 1.0 * self.size / 19

        self.grid_size = grid_size
        self.orig_sidebar_width = sidebar_width
        self.sidebar_width = sidebar_width

        self.init_pygame()

    def init_pygame(self):
        # Initialize pygame, and create the screen with additional space for the sidebar
        pygame.init()
        self.window_width = self.grid_size * (self.game.size + 1) + self.sidebar_width
        self.window_height = self.grid_size * (self.game.size + 1)
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"{self.game.name}")
        self.stone_radius = self.grid_size // 2 - 2

    def draw_current_game(self):
        font = pygame.font.SysFont(None, int(30 * self.ratio))
        text = font.render(f"{self.game.name}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(10 * self.ratio)))

    def draw_current_player(self):
        font = pygame.font.SysFont(None, int(30 * self.ratio))
        if self.game.cur_player() == Color.BLACK:
            text = font.render("Current Player: Black", True, BLACK)
        else:
            text = font.render("Current Player: White", True, WHITE)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(40 * self.ratio)))

    def draw_round(self):
        font = pygame.font.SysFont(None, int(30 * self.ratio))
        text = font.render(f"Current Round: {self.game.round}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(70 * self.ratio)))

    def draw_winner(self):
        font = pygame.font.SysFont(None, int(30 * self.ratio))
        text = font.render(f"Winner: {self.game.winner}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(100 * self.ratio)))
        if getattr(self.game, "final_score", "") != "":
            text = font.render(f"Score: {self.game.final_score}", True, BLACK)
            self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(130 * self.ratio)))

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
        # Create buttons in the sidebar
        sidebar_x = self.window_width - self.sidebar_width + int(60 * self.ratio)  # X position for all buttons
        self.buttons = [
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(480 * self.ratio),
                int(80 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Go",
                self.init_go_game,
            ),
            Button(
                sidebar_x + int(86 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(480 * self.ratio),
                int(80 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Gomoku",
                self.init_gomoku_game,
            ),
            Button(
                sidebar_x + int(172 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(480 * self.ratio),
                int(80 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Othello",
                self.init_othello_game,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(420 * self.ratio),
                int(60 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "8-way",
                self.eight_way,
            ),
            Button(
                sidebar_x + int(64 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(420 * self.ratio),
                int(60 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "9-way",
                self.nine_way,
            ),
            Button(
                sidebar_x + int(128 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(420 * self.ratio),
                int(60 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "13-way",
                self.thirteen_way,
            ),
            Button(
                sidebar_x + int(192 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(420 * self.ratio),
                int(60 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "19-way",
                self.nineteen_way,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(360 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Surrender",
                self.surrender,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(300 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Undo",
                self.undo_move,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(240 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Pass",
                self.pass_turn,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(180 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Restart",
                self.restart_game,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(120 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Save",
                lambda: self.save_game_state(f"game_state.pickle"),
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(60 * self.ratio),
                int(252 * self.ratio),
                int(50 * self.ratio),
                self.ratio,
                "Load",
                lambda: self.load_game_state("game_state.pickle"),
            ),
        ]

    def draw_buttons(self):
        # Draw buttons in the sidebar
        for button in self.buttons:
            button.draw(self.screen)

    def init_go_game(self):
        self.cur_game_type = self.game_list[0]
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def init_gomoku_game(self):
        self.cur_game_type = self.game_list[1]
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def init_othello_game(self):
        self.cur_game_type = self.game_list[2]
        self.game = self.cur_game_type(self.size)
        self.init_pygame()
        self.eight_way()

    def eight_way(self):
        self.size = 8
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def nine_way(self):
        self.size = 9
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def thirteen_way(self):
        self.size = 13
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def nineteen_way(self):
        self.size = 19
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size)
        self.init_pygame()

    def surrender(self):
        self.game.surrender()

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
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        is_handle = False
                        for button in self.buttons:
                            if button.handle_event(event):
                                is_handle = True
                        if not is_handle:
                            pos = pygame.mouse.get_pos()
                            self.handle_mouse_click(pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:
                        self.undo_move()
                    elif event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_p:
                        self.pass_turn()
                    elif event.key == pygame.K_s:
                        self.save_game_state("game_state.pickle")
                    elif event.key == pygame.K_l:
                        self.load_game_state("game_state.pickle")
                    elif event.key == pygame.K_q:
                        running = False
                self.create_buttons()
                self.draw_board()
                self.draw_current_game()
                self.draw_current_player()
                self.draw_round()
                self.draw_winner()
                self.draw_buttons()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    gui = BoardGameGUI()
    gui.start_game()
