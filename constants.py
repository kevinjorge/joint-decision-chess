import pygame

# Constants
WIDTH, HEIGHT = 800, 800
GRID_SIZE = WIDTH // 8
WHITE_SQUARE = (255, 230, 155)
BLACK_SQUARE = (140, 215, 230)
TRANSPARENT_CIRCLES = (255, 180, 155, 160)
TRANSPARENT_SPECIAL_CIRCLES = (140, 95, 80, 160)
HOVER_OUTLINE_COLOR_WHITE = (255, 240, 200)
HOVER_OUTLINE_COLOR_BLACK = (200, 235, 245)
TEXT_OFFSET = 7
HIGHLIGHT_WHITE = (255, 215, 105)
HIGHLIGHT_BLACK = (75, 215, 230)
HIGHLIGHT_WHITE_RED = (255, 100, 70)
HIGHLIGHT_BLACK_RED = (150, 60, 40)
ARROW_WHITE = (235, 180, 50, 150)
ARROW_BLACK = (0, 100, 100, 150)
ARROW_BODY_WIDTH = 20
ARROW_HEAD_HEIGHT = 35
ARROW_HEAD_WIDTH = 48
PREVIOUS_WHITE = (255, 215, 105)
PREVIOUS_BLACK = (75, 215, 230)
STARTING_PLAYER = True
INVERSE_PLAYER_VIEW = False

# Initialize Pygame to initialize fonts
pygame.init()

# Coordinate font
FONT_SIZE = 36
font = pygame.font.Font(None, FONT_SIZE) # default font is called freesansbold
COORDINATES = ['a','b','c','d','e','f','g','h']
NUMBERS = ['1','2','3','4','5','6','7','8']
white_letter_surfaces = []
black_letter_surfaces = []
number_surfaces = []
for i, letter in enumerate(COORDINATES):
    SQUARE = WHITE_SQUARE if i % 2 == 0 else BLACK_SQUARE
    white_letter_surfaces.append(font.render(letter, True, SQUARE))
    OTHER_SQUARE = BLACK_SQUARE if i % 2 == 0 else WHITE_SQUARE
    black_letter_surfaces.append(font.render(letter, True, OTHER_SQUARE))
    number_surfaces.append(font.render(NUMBERS[i], True, SQUARE))

pygame.quit()

# Chess board representation (for simplicity, just pieces are represented)
# Our convention is that white pieces are upper case.
new_board = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]