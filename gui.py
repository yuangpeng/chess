from __future__ import annotations

import copy
import sys
from time import sleep

import pygame
import pygame_gui
from loguru import logger

from account import AccountManager
from board import (
    BaseBoardGame,
    Color,
    GoGame,
    GomokuGame,
    HumanPlayerStrategy,
    Level1AIPlayerStrategy,
    Level2AIPlayerStrategy,
    Level3AIPlayerStrategy,
    OthelloGame,
)

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
    def __init__(self, grid_size: int = 40, sidebar_width: int = 300, account_file: str = "account.json"):
        # default go game with 19-way
        self.game_list: list[BaseBoardGame] = [GoGame, GomokuGame, OthelloGame]
        self.cur_game_type = self.game_list[0]
        self.size = 19
        self.game: BaseBoardGame = self.cur_game_type(self.size, HumanPlayerStrategy(Color.BLACK), HumanPlayerStrategy(Color.WHITE))

        self.ratio = 1.0 * self.size / 19

        self.grid_size = grid_size
        self.orig_sidebar_width = sidebar_width
        self.sidebar_width = sidebar_width

        self.init_pygame()
        self.account_manager = AccountManager(account_file)
        self.user1 = None
        self.user2 = None
        self.user1_login = False
        self.user2_login = False
        # Call the login method at the start
        self.login()
        if self.user1 == "AI":
            self.play1_level1_ai()
        if self.user2 == "AI":
            self.play2_level1_ai()

    def login(self):
        # Create login interface
        self.login_screen = pygame.display.set_mode((600, 250))
        self.username_input1 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((50, 50), (200, 30)), manager=self.manager)
        self.password_input1 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((50, 100), (200, 30)), manager=self.manager)
        self.login_button1 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 150), (100, 30)), text="Login", manager=self.manager)
        self.register_button1 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((150, 150), (100, 30)), text="Register", manager=self.manager)
        self.ai_button1 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 200), (100, 30)), text="AI", manager=self.manager)
        self.visitor_button1 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((150, 200), (100, 30)), text="Visitor", manager=self.manager)
        self.username_input2 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((350, 50), (200, 30)), manager=self.manager)
        self.password_input2 = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((350, 100), (200, 30)), manager=self.manager)
        self.login_button2 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 150), (100, 30)), text="Login", manager=self.manager)
        self.register_button2 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((450, 150), (100, 30)), text="Register", manager=self.manager)
        self.ai_button2 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 200), (100, 30)), text="AI", manager=self.manager)
        self.visitor_button2 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((450, 200), (100, 30)), text="Visitor", manager=self.manager)

        user1_msg = None
        user2_msg = None
        while not self.user1_login or not self.user2_login:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.manager.process_events(event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.login_button1:
                        # Validate login credentials
                        username = self.username_input1.get_text()
                        password = self.password_input1.get_text()
                        if self.account_manager.login(username, password):
                            self.user1_login = True
                            self.user1 = username
                            user1_msg = "Login successful"
                        else:
                            user1_msg = "Invalid username or password!"
                            logger.warning(user1_msg)  # Replace with a proper on-screen message
                    elif event.ui_element == self.login_button2:
                        # Validate login credentials
                        username = self.username_input2.get_text()
                        password = self.password_input2.get_text()
                        if self.account_manager.login(username, password):
                            self.user2_login = True
                            self.user2 = username
                            user2_msg = "Login successful"
                        else:
                            user2_msg = "Invalid username or password!"
                            logger.warning(user2_msg)  # Replace with a proper on-screen message
                    elif event.ui_element == self.register_button1:
                        username = self.username_input1.get_text()
                        password = self.password_input1.get_text()
                        if self.account_manager.register(username, password):
                            user1_msg = "Register successful"
                            logger.info(user2_msg)
                            self.user1_login = True
                            self.user1 = username
                        else:
                            user1_msg = "Username already exists"
                            logger.warning(user1_msg)
                    elif event.ui_element == self.register_button2:
                        username = self.username_input2.get_text()
                        password = self.password_input2.get_text()
                        if self.account_manager.register(username, password):
                            user2_msg = "Register successful"
                            logger.info(user2_msg)
                            self.user2_login = True
                            self.user2 = username
                        else:
                            user2_msg = "Username already exists"
                            logger.warning(user2_msg)
                    elif event.ui_element == self.ai_button1:
                        self.user1_login = True
                        self.user1 = "AI"
                        user1_msg = "Login successful"
                    elif event.ui_element == self.ai_button2:
                        self.user2_login = True
                        self.user2 = "AI"
                        user2_msg = "Login successful"
                    elif event.ui_element == self.visitor_button1:
                        self.user1_login = True
                        self.user1 = "Visitor"
                        user1_msg = "Login successful"
                    elif event.ui_element == self.visitor_button2:
                        self.user2_login = True
                        self.user2 = "Visitor"
                        user2_msg = "Login successful"

            self.manager.update(time_delta)
            self.login_screen.fill(BACKGROUND)
            self.manager.draw_ui(self.login_screen)

            if user1_msg is not None:
                font = pygame.font.SysFont(None, 20)
                text = font.render(f"{user1_msg}", True, BLACK)
                # Draw on the sidebar, not on the board
                self.login_screen.blit(text, pygame.Rect((50, 20), (200, 30)))
            if user2_msg is not None:
                font = pygame.font.SysFont(None, 20)
                text = font.render(f"{user2_msg}", True, BLACK)
                # Draw on the sidebar, not on the board
                self.login_screen.blit(text, pygame.Rect((350, 20), (200, 30)))

            pygame.display.flip()

        self.init_pygame()

    def init_pygame(self):
        # Initialize pygame, and create the screen with additional space for the sidebar
        pygame.init()
        self.window_width = self.grid_size * (self.game.size + 1) + self.sidebar_width
        self.window_height = self.grid_size * (self.game.size + 1)
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"{self.game.name}")
        self.stone_radius = self.grid_size // 2 - 2
        self.clock = pygame.time.Clock()
        self.manager = pygame_gui.UIManager((self.window_width, self.window_height))
        self.activate_dialog = False

    def draw_current_game(self):
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        text = font.render(f"{self.game.name}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(20 * self.ratio)))

    def draw_current_player(self):
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        if self.game.cur_player() == Color.BLACK:
            text = font.render("Current Player: Black (Player1)", True, BLACK)
        else:
            text = font.render("Current Player: White (Player2)", True, WHITE)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(50 * self.ratio)))

    def draw_player_mode(self):
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        if self.user1 == "AI" or self.user1 == "Visitor":
            role1 = self.game.player1_strategy.role
        else:
            record = self.account_manager.get_record(self.user1)
            role1 = (
                self.user1
                + f"({record['go_wins']}/{record['go_games_played']}, {record['gomoku_wins']}/{record['gomoku_games_played']}, {record['othello_wins']}/{record['othello_games_played']})"
            )
        text = font.render(f"Player1 Mode: {role1}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(80 * self.ratio)))

        if self.user2 == "AI" or self.user2 == "Visitor":
            role2 = self.game.player2_strategy.role
        else:
            record = self.account_manager.get_record(self.user2)
            role2 = (
                self.user2
                + f"({record['go_wins']}/{record['go_games_played']}, {record['gomoku_wins']}/{record['gomoku_games_played']}, {record['othello_wins']}/{record['othello_games_played']})"
            )
        text = font.render(f"Player2 Mode: {role2}", True, WHITE)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(110 * self.ratio)))

    def draw_round(self):
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        text = font.render(f"Current Round: {self.game.round}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(140 * self.ratio)))

    def draw_winner(self):
        font = pygame.font.SysFont(None, int(24 * self.ratio))
        text = font.render(f"Winner: {self.game.winner}", True, BLACK)
        # Draw on the sidebar, not on the board
        self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(170 * self.ratio)))
        if getattr(self.game, "final_score", "") != "":
            text = font.render(f"Score: {self.game.final_score}", True, BLACK)
            self.screen.blit(text, (self.window_width - self.sidebar_width + int(5 * self.ratio), int(200 * self.ratio)))

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
                self.window_height - int(560 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Re-login",
                self.__init__,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(520 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Playback",
                self.playback,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(480 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Human",
                self.play1_human,
            ),
            Button(
                sidebar_x + int(130 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(480 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Human",
                self.play2_human,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(440 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level1 AI",
                self.play1_level1_ai,
            ),
            Button(
                sidebar_x + int(130 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(440 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level1 AI",
                self.play2_level1_ai,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(400 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level2 AI",
                self.play1_level2_ai,
            ),
            Button(
                sidebar_x + int(130 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(400 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level2 AI",
                self.play2_level2_ai,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(360 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level3 AI",
                self.play1_level3_ai,
            ),
            Button(
                sidebar_x + int(130 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(360 * self.ratio),
                int(122 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Level3 AI",
                self.play2_level3_ai,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(320 * self.ratio),
                int(80 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Go",
                self.init_go_game,
            ),
            Button(
                sidebar_x + int(86 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(320 * self.ratio),
                int(80 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Gomoku",
                self.init_gomoku_game,
            ),
            Button(
                sidebar_x + int(172 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(320 * self.ratio),
                int(80 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Othello",
                self.init_othello_game,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(280 * self.ratio),
                int(60 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "8-way",
                self.eight_way,
            ),
            Button(
                sidebar_x + int(64 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(280 * self.ratio),
                int(60 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "9-way",
                self.nine_way,
            ),
            Button(
                sidebar_x + int(128 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(280 * self.ratio),
                int(60 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "13-way",
                self.thirteen_way,
            ),
            Button(
                sidebar_x + int(192 * self.ratio) - int(30 * self.ratio),
                self.window_height - int(280 * self.ratio),
                int(60 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "19-way",
                self.nineteen_way,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(240 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Surrender",
                self.surrender,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(200 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Undo",
                self.undo_move,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(160 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Pass",
                self.pass_turn,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(120 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Restart",
                self.restart_game,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(80 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Save",
                self.open_save_dialog,
            ),
            Button(
                sidebar_x - int(30 * self.ratio),
                self.window_height - int(40 * self.ratio),
                int(252 * self.ratio),
                int(30 * self.ratio),
                self.ratio,
                "Load",
                self.open_load_dialog,
            ),
        ]

    def playback(self):
        replay_back = copy.deepcopy(self.game.replay)
        self.game.__init__(self.size, self.game.player1_strategy, self.game.player2_strategy)
        for move in replay_back:
            sleep(0.5)
            self.update_gui()
            self.game.move(move)

    def open_save_dialog(self):
        # Create a file dialog to save the file
        self.save_dialog = pygame_gui.windows.UIFileDialog(
            rect=pygame.Rect((100, 100), (400, 500)),
            manager=self.manager,
            window_title="Save Game State",
            initial_file_path="game_state.pickle",
            allow_existing_files_only=False,
        )
        self.activate_dialog = True

    def open_load_dialog(self):
        # Create a file dialog to load the file
        self.load_dialog = pygame_gui.windows.UIFileDialog(
            rect=pygame.Rect((100, 100), (400, 500)),
            manager=self.manager,
            window_title="Load Game State",
            initial_file_path="game_state.pickle",
            allow_existing_files_only=True,
        )
        self.activate_dialog = True

    def draw_buttons(self):
        # Draw buttons in the sidebar
        for button in self.buttons:
            button.draw(self.screen)

    def init_go_game(self):
        self.cur_game_type = self.game_list[0]
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def init_gomoku_game(self):
        self.cur_game_type = self.game_list[1]
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def init_othello_game(self):
        self.cur_game_type = self.game_list[2]
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()
        self.eight_way()

    def eight_way(self):
        self.size = 8
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def nine_way(self):
        self.size = 9
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def thirteen_way(self):
        self.size = 13
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def nineteen_way(self):
        self.size = 19
        self.ratio = 1.0 * self.size / 19
        self.sidebar_width = self.orig_sidebar_width * self.ratio
        self.game = self.cur_game_type(self.size, self.game.player1_strategy, self.game.player2_strategy)
        self.init_pygame()

    def play1_human(self):
        if self.user1 != "AI":
            self.game.player1_strategy = HumanPlayerStrategy(Color.BLACK)

    def play1_level1_ai(self):
        if self.user1 == "AI":
            self.game.player1_strategy = Level1AIPlayerStrategy(Color.BLACK)

    def play1_level2_ai(self):
        if self.user1 == "AI":
            self.game.player1_strategy = Level2AIPlayerStrategy(Color.BLACK)

    def play1_level3_ai(self):
        if self.user1 == "AI":
            self.game.player1_strategy = Level3AIPlayerStrategy(Color.BLACK)

    def play2_human(self):
        if self.user2 != "AI":
            self.game.player2_strategy = HumanPlayerStrategy(Color.WHITE)

    def play2_level1_ai(self):
        if self.user2 == "AI":
            self.game.player2_strategy = Level1AIPlayerStrategy(Color.WHITE)

    def play2_level2_ai(self):
        if self.user2 == "AI":
            self.game.player2_strategy = Level2AIPlayerStrategy(Color.WHITE)

    def play2_level3_ai(self):
        if self.user2 == "AI":
            self.game.player2_strategy = Level3AIPlayerStrategy(Color.WHITE)

    def surrender(self):
        self.game.surrender()

    def undo_move(self):
        self.game.regret()

    def restart_game(self):
        self.game.restart()
        self.update_record = False

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
            self.game.cur_player_strategy().get_move((row, col))
            return True
        return False

    def update_gui(self):
        self.create_buttons()
        self.draw_board()
        self.draw_current_game()
        self.draw_current_player()
        self.draw_player_mode()
        self.draw_round()
        self.draw_winner()
        self.draw_buttons()
        self.manager.update(self.clock.tick(60) / 1000.0)
        self.manager.draw_ui(self.screen)  # Draw the UI
        pygame.display.flip()

    def start_game(self):
        running = True
        block = False
        self.update_record = False
        while running:
            for event in pygame.event.get():
                if getattr(self, "save_dialog", None):
                    if len(self.save_dialog.groups()) == 0:
                        # del self.save_dialog
                        self.activate_dialog = False
                if getattr(self, "load_dialog", None):
                    if len(self.load_dialog.groups()) == 0:
                        # del self.load_dialog
                        self.activate_dialog = False
                self.manager.process_events(event)
                # Handle the save and load dialog events
                if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                    if event.ui_element == getattr(self, "save_dialog", None):
                        self.save_game_state(event.text)
                        del self.save_dialog
                    elif event.ui_element == getattr(self, "load_dialog", None):
                        self.load_game_state(event.text)
                        del self.load_dialog
                    self.activate_dialog = False
                elif event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.activate_dialog:
                        continue
                    if event.button == 1:
                        is_handle = False
                        for button in self.buttons:
                            if button.handle_event(event):
                                is_handle = True
                        if not is_handle:
                            pos = pygame.mouse.get_pos()
                            if self.game.cur_player_strategy().role == "Human":
                                if self.handle_mouse_click(pos):
                                    self.game.play_round()
                elif event.type == pygame.KEYDOWN:
                    if self.activate_dialog:
                        continue
                    if event.key == pygame.K_u:
                        self.undo_move()
                    elif event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_p:
                        self.pass_turn()
                    elif event.key == pygame.K_s:
                        self.open_save_dialog()
                    elif event.key == pygame.K_l:
                        self.open_load_dialog()
                    elif event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_t:
                        block = True
                    elif event.key == pygame.K_c:
                        block = False
                self.update_gui()

            if block:
                continue
            if self.game.game_over and not self.update_record:
                self.update_record = True
                if self.user1 != "AI" and self.user1 != "Visitor":
                    self.account_manager.update_record(self.user1, self.game.name.split(" ")[0].lower(), self.game.winner == "Black")
                if self.user2 != "AI" and self.user2 != "Visitor":
                    self.account_manager.update_record(self.user2, self.game.name.split(" ")[0].lower(), self.game.winner == "White")
            if "AI" in self.game.cur_player_strategy().role:
                sleep(0.01)
                self.game.play_round()
                self.update_gui()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    gui = BoardGameGUI()
    gui.start_game()
