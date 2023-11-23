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


def check_liberties(board, row, col, color):
    """Recursively check if a group of stones has any liberties."""
    if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
        return False
    if board[row][col] is None:
        return True
    if board[row][col] != color:
        return False
    # Temporarily mark the stone to avoid repeated checks
    board[row][col] = "checked"
    # Check all adjacent points
    if (
        check_liberties(board, row - 1, col, color)
        or check_liberties(board, row + 1, col, color)
        or check_liberties(board, row, col - 1, color)
        or check_liberties(board, row, col + 1, color)
    ):
        return True
    return False


def capture_stones(board, row, col, color):
    """Remove a group of stones if they have no liberties."""
    if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
        return
    if board[row][col] != "checked":
        return
    board[row][col] = None  # Remove the stone
    # Continue with the rest of the group
    capture_stones(board, row - 1, col, color)
    capture_stones(board, row + 1, col, color)
    capture_stones(board, row, col - 1, color)
    capture_stones(board, row, col + 1, color)


def check_for_captures(board, last_move_row, last_move_col):
    """Check for captures after a stone is placed."""
    # Check all adjacent points for captures
    for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        adj_row = last_move_row + d_row
        adj_col = last_move_col + d_col
        if 0 <= adj_row < BOARD_SIZE and 0 <= adj_col < BOARD_SIZE and board[adj_row][adj_col] is not None:
            color = board[adj_row][adj_col]
            if not check_liberties(board, adj_row, adj_col, color):
                capture_stones(board, adj_row, adj_col, color)
    # Restore the original colors after checking for captures
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == "checked":
                board[row][col] = color


# Initialize pygame
pygame.init()

# Create the screen
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Go Game")

# Initialize the board
board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
current_color = BLACK


def draw_board():
    screen.fill(BACKGROUND)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            pygame.draw.rect(screen, BLACK, (GRID_SIZE + col * GRID_SIZE - 1, GRID_SIZE + row * GRID_SIZE - 1, 2, 2))
            if board[row][col] in (BLACK, WHITE):
                pygame.draw.circle(screen, board[row][col], (GRID_SIZE + col * GRID_SIZE, GRID_SIZE + row * GRID_SIZE), STONE_RADIUS)


def handle_mouse_click(pos):
    global current_color
    x, y = pos
    row = round((y - GRID_SIZE) / GRID_SIZE)
    col = round((x - GRID_SIZE) / GRID_SIZE)

    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and board[row][col] is None:
        board[row][col] = current_color
        check_for_captures(board, row, col)  # Check for captures after the move
        current_color = WHITE if current_color == BLACK else BLACK
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
