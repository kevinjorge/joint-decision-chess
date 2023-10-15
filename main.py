import pygame
import sys
import json
import asyncio
import pygbag.aio as asyncio
import pygbag_net
import builtins
from game import *
from constants import *
from helpers import *

# Handle Persistent Storage
if __import__("sys").platform == "emscripten":
    from platform import window

# Initialize Pygame
pygame.init()

current_theme = Theme()

with open('themes.json', 'r') as file:
    themes = json.load(file)

# Initialize Pygame window
game_window = pygame.display.set_mode((current_theme.WIDTH, current_theme.HEIGHT))

# Load the chess pieces dynamically
pieces = {}
transparent_pieces = {}
for color in ['w', 'b']:
    for piece_lower in ['r', 'n', 'b', 'q', 'k', 'p']:
        piece_key, image_name_key = name_keys(color, piece_lower)
        pieces[piece_key], transparent_pieces[piece_key] = load_piece_image(image_name_key, current_theme.GRID_SIZE)

# Main loop piece selection logic that updates state
def handle_new_piece_selection(game, row, col, is_white, hovered_square):
    piece = game.board[row][col]
    # Initialize variables based on turn
    if game._starting_player == is_white or game._debug:
        first_intent = True
        selected_piece = (row, col)
        selected_piece_image = transparent_pieces[piece]
        valid_moves, valid_captures, valid_specials = calculate_moves(game.board, row, col, game.moves, game.castle_attributes)
    else:
        first_intent = False
        selected_piece = None
        selected_piece_image = None
        valid_moves, valid_captures, valid_specials = [], [], []

    # Remove invalid moves that place the king under check
    for move in valid_moves.copy():
        # Before making the move, create a copy of the board where the piece has moved
        temp_board = [rank[:] for rank in game.board]  
        temp_moves = game.moves.copy()
        temp_moves.append(output_move(piece, selected_piece, move[0], move[1], temp_board[move[0]][move[1]]))
        temp_board[move[0]][move[1]] = temp_board[selected_piece[0]][selected_piece[1]]
        temp_board[selected_piece[0]][selected_piece[1]] = ' '
        
        # Temporary invalid move check, Useful for my variant later
        if is_invalid_capture(temp_board, not is_white):
            valid_moves.remove(move)
            if move in valid_captures:
                valid_captures.remove(move)
        elif is_check(temp_board, is_white, temp_moves):
            valid_moves.remove(move)
            if move in valid_captures:
                valid_captures.remove(move)
    
    for move in valid_specials.copy():
        # Castling moves are already validated in calculate moves, this is only for enpassant
        if (move[0], move[1]) not in [(7, 2), (7, 6), (0, 2), (0, 6)]:
            temp_board = [rank[:] for rank in game.board]  
            temp_moves = game.moves.copy()
            temp_moves.append(output_move(piece, selected_piece, move[0], move[1], temp_board[move[0]][move[1]], 'enpassant'))
            temp_board[move[0]][move[1]] = temp_board[selected_piece[0]][selected_piece[1]]
            temp_board[selected_piece[0]][selected_piece[1]] = ' '
            capture_row = 4 if move[0] == 3 else 5
            temp_board[capture_row][move[1]] = ' '
            if is_check(temp_board, is_white, temp_moves):
                valid_specials.remove(move)
    
    if (row, col) != hovered_square:
        hovered_square = (row, col)
    
    return first_intent, selected_piece, selected_piece_image, valid_moves, valid_captures, valid_specials, hovered_square

# Main loop piece move selection logic that updates state
def handle_piece_move(game, selected_piece, row, col, valid_captures):
    # Initialize Variables
    promotion_square = None
    promotion_required = False
    # Need to be considering the selected piece for this section not an old piece
    piece = game.board[selected_piece[0]][selected_piece[1]]
    is_white = piece.isupper()

    temp_board = [rank[:] for rank in game.board]  
    temp_moves = game.moves.copy()
    temp_moves.append(output_move(piece, selected_piece, row, col, temp_board[row][col]))
    temp_board[row][col] = temp_board[selected_piece[0]][selected_piece[1]]
    temp_board[selected_piece[0]][selected_piece[1]] = ' '

    # Move the piece if the king does not enter check
    if not is_check(temp_board, is_white, temp_moves):
        game.update_state(row, col, selected_piece)
        if piece.lower() != 'p' or (piece.lower() == 'p' and (row != 7 and row != 0)):
            print("ALG_MOVES:", game.alg_moves)
        
        if (row, col) in valid_captures:
            capture_sound.play()
        else:
            move_sound.play()
        
        selected_piece = None

        checkmate, remaining_moves = is_checkmate_or_stalemate(game.board, not is_white, game.moves)
        if checkmate:
            print("CHECKMATE")
            game.end_position = True
            game.add_end_game_notation(checkmate)
            return None, promotion_required
        elif remaining_moves == 0:
            print("STALEMATE")
            game.end_position = True
            game.add_end_game_notation(checkmate)
            return None, promotion_required
        elif game.threefold_check():
            print("STALEMATE BY THREEFOLD REPETITION")
            game.forced_end = "Stalemate by Threefold Repetition"
            game.end_position = True
            game.add_end_game_notation(checkmate)
            return None, promotion_required

    # Pawn Promotion
    if game.board[row][col].lower() == 'p' and (row == 0 or row == 7):
        promotion_required = True
        promotion_square = (row, col)

    return promotion_square, promotion_required

# Main loop piece special move selection logic that updates state
def handle_piece_special_move(game, selected_piece, row, col):
    # Need to be considering the selected piece for this section not an old piece
    piece = game.board[selected_piece[0]][selected_piece[1]]
    is_white = piece.isupper()

    # Castling and Enpassant moves are already validated, we simply update state
    game.update_state(row, col, selected_piece, special=True)
    print("ALG_MOVES:", game.alg_moves)
    if (row, col) in [(7, 2), (7, 6), (0, 2), (0, 6)]:
        move_sound.play()
    else:
        capture_sound.play()

    checkmate, remaining_moves = is_checkmate_or_stalemate(game.board, not is_white, game.moves)
    if checkmate:
        print("CHECKMATE")
        game.end_position = True
        game.add_end_game_notation(checkmate)
        return piece, is_white
    elif remaining_moves == 0:
        print("STALEMATE")
        game.end_position = True
        game.add_end_game_notation(checkmate)
        return piece, is_white
    elif game.threefold_check():
        print("STALEMATE BY THREEFOLD REPETITION")
        game.forced_end = "Stalemate by Threefold Repetition"
        game.end_position = True
        game.add_end_game_notation(checkmate)
        return piece, is_white

    return piece, is_white

# Command-Action synchronization function
def handle_command(status_names, client_state_actions, web_metadata_dict, games_metadata_name, game_tab_id):
    command_name, client_action_name, client_executed_name, *remaining = status_names
    if len(status_names) == 3:
        client_reset_name = None 
    else:
        client_reset_name = remaining[0]
    client_executed_status, client_reset_status = \
        client_state_actions[client_executed_name], client_state_actions.get(client_reset_name)
    
    status_metadata_dict = web_metadata_dict[game_tab_id]
    if status_metadata_dict.get(command_name) is not None:
        # Command to execute is received and no update is sent
        if status_metadata_dict[command_name]['execute'] and not status_metadata_dict[command_name]['update_executed'] and not client_reset_status:
            if client_state_actions[client_action_name] != True:
                client_state_actions[client_action_name] = True
            if client_executed_status:
                status_metadata_dict[command_name]['update_executed'] = True
                web_metadata_dict[game_tab_id] = status_metadata_dict
                json_metadata = json.dumps(web_metadata_dict)
                
                window.localStorage.setItem(games_metadata_name, json_metadata)
                client_state_actions[client_action_name] = False

        # Handling race conditions assuming speed differences and sychronizing states with this.
        # That is only once we stop receiving the command, after an execution, do we allow it to be executed again
        if client_executed_status and not status_metadata_dict[command_name]['execute']:
            client_state_actions[client_executed_name] = False    

        if client_reset_status is not None and client_reset_status == True and not status_metadata_dict[command_name]['reset']:
            status_metadata_dict[command_name]['reset'] = True
            status_metadata_dict[command_name]['execute'] = False
            web_metadata_dict[game_tab_id] = status_metadata_dict
            json_metadata = json.dumps(web_metadata_dict)
            
            window.localStorage.setItem(games_metadata_name, json_metadata)
            client_state_actions[client_reset_name] = False
            client_state_actions[client_action_name] = False

# Game State loop for promotion
async def promotion_state(promotion_square, client_game, row, col, draw_board_params, client_state_actions, command_status_names, drawing_settings, game_tab_id):
    promotion_buttons = display_promotion_options(current_theme, promotion_square[0], promotion_square[1])
    promoted, promotion_required, end_state = False, True, None
    
    while promotion_required:
        for event in pygame.event.get():
            for button in promotion_buttons:
                button.handle_event(event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if button.rect.collidepoint(x, y):
                        client_game.promote_to_piece(row, col, button.piece)
                        promotion_required = False  # Exit promotion state condition
                        promoted = True
        # if client_state_actions["undo"]:
        #     # Update current and previous position highlighting
        #     client_game.undo_move() # TODO Should undo three times in promotion only
        #     promotion_required = False
        #     client_state_actions["undo"] = False
        #     client_state_actions["undo_executed"] = True
        
        if client_state_actions["resign"]:
            client_game.undo_move()
            client_game.forced_end = "White Resigned" if client_game.current_turn else "Black Resigned"
            print(client_game.forced_end)
            client_game.end_position = True
            client_game.add_end_game_notation(True)
            promotion_required = False
            end_state = True
            client_state_actions["resign"] = False
            client_state_actions["resign_executed"] = True

        # if client_state_actions["draw_offer"] and not client_state_actions["draw_offer_sent"]:
        #     offer_data = {node.CMD: "draw_offer"}
        #     node.tx(offer_data, shm=True)
        #     client_state_actions["draw_offer_sent"] = True
        # if client_state_actions["draw_accept"]:
        #     if not client_state_actions["draw_offer_sent"]:
        #         offer_data = {node.CMD: "draw_accept"}
        #         node.tx(offer_data, shm=True)
        #     if client_state_actions["draw_offer_sent"] or client_state_actions["draw_offer_received"]:
        #         client_game.undo_move()
        #         promotion_required = False
        #         end_state = True
        #         client_game.forced_end = "Draw by mutual agreement"
        #         print(client_game.forced_end)
        #         running = False
        #         client_game.end_position = True
        #         client_game.add_end_game_notation(False)
        #         if client_state_actions["draw_offer_received"]:
        #             action, executed = "draw_accept", "draw_accept_executed"
        #             client_state_actions["draw_offer_received"] = False
        #         elif client_state_actions["draw_offer_sent"]:
        #             action, executed = "draw_offer", "draw_offer_executed"
        #             client_state_actions["draw_offer_sent"] = False
        #             client_state_actions["draw_accept"] = False
        #         # This keeps being set on loop potentially also sent is never set to false
        #         client_state_actions[action] = False
        #         client_state_actions[executed] = True
        # if client_state_actions["draw_deny"]:
        #     reset_data = {node.CMD: "reset"}
        #     node.tx(reset_data, shm=True)
        #     client_state_actions["draw_deny"] = False
        #     client_state_actions["draw_deny_executed"] = True
        #     client_state_actions["draw_offer_received"] = False
        #     window.sessionStorage.setItem("draw_request", "false")

        # Theme cycle
        if client_state_actions["cycle_theme"]:
            drawing_settings["theme_index"] += 1
            drawing_settings["theme_index"] %= len(themes)
            current_theme.apply_theme(themes[drawing_settings["theme_index"]])
            # Redraw board and coordinates
            drawing_settings["chessboard"] = generate_chessboard(current_theme)
            drawing_settings["coordinate_surface"] = generate_coordinate_surface(current_theme)
            client_state_actions["cycle_theme"] = False
            client_state_actions["cycle_theme_executed"] = True

        if client_state_actions["flip"]:
            current_theme.INVERSE_PLAYER_VIEW = not current_theme.INVERSE_PLAYER_VIEW
            # Redraw board and coordinates
            drawing_settings["chessboard"] = generate_chessboard(current_theme)
            drawing_settings["coordinate_surface"] = generate_coordinate_surface(current_theme)
            client_state_actions["flip"] = False
            client_state_actions["flip_executed"] = True

        # Clear the screen
        game_window.fill((0, 0, 0))
        
        # Draw the board, we need to copy the params else we keep mutating them with each call for inverse board draws
        draw_board(draw_board_params.copy())
        
        # Darken the screen
        overlay = pygame.Surface((current_theme.WIDTH, current_theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))

        # Blit the overlay surface onto the main window
        game_window.blit(overlay, (0, 0))

        # Draw buttons and update the display
        for button in promotion_buttons:
            img = pieces[button.piece]
            img_x, img_y = button.rect.x, button.rect.y
            if button.is_hovered:
                img = pygame.transform.smoothscale(img, (current_theme.GRID_SIZE * 1.5, current_theme.GRID_SIZE * 1.5))
                img_x, img_y = button.scaled_x, button.scaled_y
            game_window.blit(img, (img_x, img_y))

        web_game_metadata = window.localStorage.getItem("web_game_metadata")

        web_game_metadata_dict = json.loads(web_game_metadata)

        # DEV logs to console
        # web_game_metadata_dict['console_messages'] = console_log_messages

        # TODO Can just put this into an asynchronous loop if I wanted or needed
        # Undo move, resign, draw offer, cycle theme, flip command handle
        for status_names in command_status_names:
            handle_command(status_names, client_state_actions, web_game_metadata_dict, "web_game_metadata", game_tab_id)     

        pygame.display.flip()
        await asyncio.sleep(0)

    return promoted, end_state

class Node(pygbag_net.Node):
    ...

# Main loop
async def main():
    builtins.node = Node(gid=222, groupname="Simple Chess Board", offline="offline" in sys.argv)
    node = builtins.node
    running, waiting, initializing, initialized = True, True, False, False
    # Web Browser actions affect these only. Even if players try to alter it, 
    # It simply enables the buttons or does a local harmless action
    # The following are client-side status variables, the first is whether an action should be performed,
    # the second on whether an action has been performed, the optional reset variable is unimplemented but indicates whether an action has been aborted
    # based on other multiplayer actions. It will be necessary.
    client_state_actions = {
        "undo": False,
        "undo_executed": False,
        "undo_sent": False,
        "undo_received": False,
        "undo_response_received": False,
        "undo_reset": False,
        "undo_accept": False,
        "undo_accept_executed": False,
        "undo_accept_reset": False,
        "undo_deny": False,
        "undo_deny_executed": False,
        "undo_deny_reset": False,
        "cycle_theme": False,
        "cycle_theme_executed": False,
        "resign": False,
        "resign_executed": False,
        "resign_reset": False,
        "draw_offer": False,
        "draw_offer_executed": False,
        "draw_offer_sent": False,
        "draw_offer_received": False,
        "draw_response_received": False,
        "draw_offer_reset": False,
        "draw_accept": False,
        "draw_accept_executed": False,
        "draw_accept_reset": False,
        "draw_deny": False,
        "draw_deny_executed": False,
        "draw_deny_reset": False,
        "flip": False,
        "flip_executed": False,
    }
    # This holds the command name for the web and the associated keys in the dictionary
    command_status_names = [
        ("undo_move", "undo", "undo_executed", "undo_reset"),
        ("undo_move_accept", "undo_accept", "undo_accept_executed", "undo_accept_reset"),
        ("undo_move_deny", "undo_deny", "undo_deny_executed", "undo_deny_reset"),
        ("undo_move", "undo", "undo_executed", "undo_reset"),
        ("draw_offer", "draw_offer", "draw_offer_executed", "draw_offer_reset"),
        ("draw_offer_accept", "draw_accept", "draw_accept_executed", "draw_accept_reset"),
        ("draw_offer_deny", "draw_deny", "draw_deny_executed", "draw_deny_reset"),
        ("resign", "resign", "resign_executed"),
        ("cycle_theme", "cycle_theme", "cycle_theme_executed"),
        ("flip_board", "flip", "flip_executed")
    ]
    offers = command_status_names[:4]

    request_mapping = [
        ["undo_move_accept","undo_request"], 
        ["undo_move_deny","undo_request"],
        ["draw_offer_accept","draw_request"], 
        ["draw_offer_deny","draw_request"]
    ]

    for i in range(len(offers)):
        for associated in request_mapping:
            if offers[i][0] == associated[0]:
                offers[i] += (associated[1],)
    console_log_messages = []

    selected_piece = None
    hovered_square = None
    current_right_clicked_square = None
    end_right_released_square = None
    right_clicked_squares = []
    drawn_arrows = []
    # Boolean stating the first intention of moving a piece
    first_intent = False
    selected_piece_image = None
    # Locks the game state due to pawn promotion
    promotion_required = False
    promotion_square = None
    valid_moves = []
    valid_captures = []
    valid_specials = []

    left_mouse_button_down = False
    right_mouse_button_down = False

    # Only draw these surfaces as needed; once per selection of theme
    drawing_settings = {
        "chessboard": generate_chessboard(current_theme),
        "coordinate_surface": generate_coordinate_surface(current_theme),
        "theme_index": 0
    }

    # Main game loop
    while running:
        # Network events
        for ev in node.get_events():
            try:
                if ev == node.SYNC:
                    print("SYNC:", node.proto, node.data[node.CMD])
                    cmd = node.data[node.CMD]
                    if cmd == "initialize":
                        starting_player = node.data.pop("start")
                        initializing = True
                        sent = int(not starting_player)
                    elif cmd == f"{opponent} ready":
                        waiting = False
                    elif f"{opponent}_update" in cmd or "_sync" in cmd:
                        if f"{opponent}_update" in cmd:
                            game = Game(custom_params=json.loads(node.data.pop("game")))
                            if client_game._sync:
                                if (len(game.alg_moves) > len(client_game.alg_moves)) or (len(game.alg_moves) < len(client_game.alg_moves) and game._move_undone) or \
                                    game.end_position:
                                        client_game.synchronize(game)
                                        sent = 0
                                        if client_game.alg_moves != []:
                                            if not any(symbol in client_game.alg_moves[-1] for symbol in ['0-1', '1-0', '½–½']): # Could add a winning or losing sound
                                                if "x" not in client_game.alg_moves[-1]:
                                                    move_sound.play()
                                                else:
                                                    capture_sound.play()
                                            if client_game.end_position:
                                                running = False
                                                is_white = True
                                                checkmate, remaining_moves = is_checkmate_or_stalemate(client_game.board, is_white, client_game.moves)
                                                if checkmate:
                                                    print("CHECKMATE")
                                                elif remaining_moves == 0:
                                                    print("STALEMATE")
                                                elif client_game.threefold_check():
                                                    print("DRAW BY THREEFOLD REPETITION")
                                                elif client_game.forced_end != "":
                                                    print(client_game.forced_end)
                                                print("ALG_MOVES: ", client_game.alg_moves)
                                                break
                                            print("ALG_MOVES: ", client_game.alg_moves)
                        if "_sync" in cmd:
                            # Need to set game here if no update cmd is trigerred, else we have an old game
                            if "game" in node.data:
                                game = Game(custom_params=json.loads(node.data.pop("game")))
                            if game.board == client_game.board and not client_game._sync:
                                print(f"Syncing {player.capitalize()}...")
                                client_game._sync = True
                                client_game._move_undone = False
                                your_turn = client_game.current_turn == client_game._starting_player
                                sent = 0 if your_turn else 1
                            # elif both games are unsynced, synchronize and send something to halt infinite sync signals?
                            elif "req_sync" in cmd:
                                txdata = {node.CMD: f"_sync"}
                                send_game = client_game.to_json()
                                print(client_game._sync)
                                txdata.update({"game": send_game})
                                node.tx(txdata, shm=True)
                                your_turn = client_game.current_turn == client_game._starting_player
                                sent = 0 if your_turn else 1
                    elif cmd == "draw_offer":
                        if not client_state_actions["draw_offer_sent"]:
                            window.sessionStorage.setItem("draw_request", "true")
                            client_state_actions["draw_offer_received"] = True
                    elif cmd == "draw_accept":
                        client_state_actions["draw_response_received"] = True
                    elif cmd == "undo_offer":
                        if not client_state_actions["undo_sent"]:
                            window.sessionStorage.setItem("undo_request", "true")
                            client_state_actions["undo_received"] = True
                    elif cmd == "undo_accept":
                        client_state_actions["undo_response_received"] = True
                    elif cmd == "reset":
                        for offer_states in offers:
                            if client_state_actions[offer_states[1]] == True or len(offer_states) == 5:
                                if len(offer_states) == 5:
                                    window.sessionStorage.setItem(offer_states[-1], "false")
                                client_state_actions[offer_states[1]] = False 
                                client_state_actions[offer_states[3]] = True 
                                if "accept" not in offer_states[1] and "deny" not in offer_states[1]:
                                    sent_status = offer_states[1] + "_sent"
                                    received_status = offer_states[1] + "_received"
                                    client_state_actions[sent_status] = False
                                    client_state_actions[received_status] = False

                elif ev == node.GAME:
                    print("GAME:", node.proto, node.data[node.CMD])
                    cmd = node.data[node.CMD]

                    if cmd == f"{opponent} initialized":
                        node.tx({node.CMD: f"{player} ready"})
                        waiting = False
                    elif f"{opponent}_update" in cmd or "_sync" in cmd:
                        if f"{opponent}_update" in cmd:
                            game = Game(custom_params=json.loads(node.data.pop("game")))
                            if client_game._sync:
                                if (len(game.alg_moves) > len(client_game.alg_moves)) or (len(game.alg_moves) < len(client_game.alg_moves) and game._move_undone) or \
                                    game.end_position:
                                        client_game.synchronize(game)
                                        sent = 0
                                        if client_game.alg_moves != []:
                                            if not any(symbol in client_game.alg_moves[-1] for symbol in ['0-1', '1-0', '½–½']): # Could add a winning or losing sound
                                                if "x" not in client_game.alg_moves[-1]:
                                                    move_sound.play()
                                                else:
                                                    capture_sound.play()
                                            if client_game.end_position:
                                                running = False
                                                is_white = True
                                                checkmate, remaining_moves = is_checkmate_or_stalemate(client_game.board, is_white, client_game.moves)
                                                if checkmate:
                                                    print("CHECKMATE")
                                                elif remaining_moves == 0:
                                                    print("STALEMATE")
                                                elif client_game.threefold_check():
                                                    print("DRAW BY THREEFOLD REPETITION")
                                                elif client_game.forced_end != "":
                                                    print(client_game.forced_end)
                                                print("ALG_MOVES: ", client_game.alg_moves)
                                                break
                                            print("ALG_MOVES: ", client_game.alg_moves)
                        if "_sync" in cmd:
                            # Need to set game here if no update cmd is triggered, else we have an old game
                            if "game" in node.data:
                                game = Game(custom_params=json.loads(node.data.pop("game")))
                            if game.board == client_game.board and not client_game._sync:
                                print(f"Syncing {player.capitalize()}...")
                                client_game._sync = True
                                client_game._move_undone = False
                                your_turn = client_game.current_turn == client_game._starting_player
                                sent = 0 if your_turn else 1
                            # elif both games are unsynced, synchronize? and maybe or maybe not send something to halt infinite sync signals?
                            elif "req_sync" in cmd:
                                txdata = {node.CMD: f"_sync"}
                                send_game = client_game.to_json()
                                txdata.update({"game": send_game})
                                node.tx(txdata, shm=True)
                                your_turn = client_game.current_turn == client_game._starting_player
                                sent = 0 if your_turn else 1
                    elif cmd == "draw_offer":
                        if not client_state_actions["draw_offer_sent"]:
                            window.sessionStorage.setItem("draw_request", "true")
                            client_state_actions["draw_offer_received"] = True
                    elif cmd == "draw_accept":
                        client_state_actions["draw_response_received"] = True
                    elif cmd == "undo_offer":
                        if not client_state_actions["undo_sent"]:
                            window.sessionStorage.setItem("undo_request", "true")
                            client_state_actions["undo_received"] = True
                    elif cmd == "undo_accept":
                        client_state_actions["undo_response_received"] = True
                    elif cmd == "reset":
                        for offer_states in offers:
                            if client_state_actions[offer_states[1]] == True or len(offer_states) == 5:
                                if len(offer_states) == 5:
                                    window.sessionStorage.setItem(offer_states[-1], "false")
                                client_state_actions[offer_states[1]] = False 
                                client_state_actions[offer_states[3]] = True 
                                if "accept" not in offer_states[1] and "deny" not in offer_states[1]:
                                    sent_status = offer_states[1] + "_sent"
                                    received_status = offer_states[1] + "_received"
                                    client_state_actions[sent_status] = False
                                    client_state_actions[received_status] = False
                    elif cmd == "clone":
                        # send all history to child
                        node.checkout_for(node.data)
                        starting_player = True
                        node.tx({node.CMD: "initialize", "start": not starting_player})
                        initializing = True
                        sent = int(not starting_player)

                    elif cmd == "ingame":
                        print("TODO: join game")
                    else:
                        print("87 ?", node.data)

                elif ev == node.CONNECTED:
                    print(f"CONNECTED as {node.nick}")

                elif ev == node.JOINED:
                    print("Entered channel", node.joined)
                    if node.joined == node.lobby_channel:
                        node.tx({node.CMD: "ingame", node.PID: node.pid})

                elif ev == node.TOPIC:
                    print(f'[{node.channel}] TOPIC "{node.topics[node.channel]}"')

                elif ev in [node.LOBBY, node.LOBBY_GAME]:
                    cmd, pid, nick, info = node.proto

                    if cmd == node.HELLO:
                        print("Lobby/Game:", "Welcome", nick)
                        # publish if main
                        if not node.fork:
                            node.publish()

                    elif (ev == node.LOBBY_GAME) and (cmd == node.OFFER):
                        if node.fork:
                            print("cannot fork, already a clone/fork pid=", node.fork)
                        elif len(node.pstree[node.pid]["forks"]):
                            print("cannot fork, i'm main for", node.pstree[node.pid]["forks"])
                        else:
                            print("forking to game offer", node.hint)
                            node.clone(pid)
                            print("cloning", player, pid)

                    else:
                        print(f"\nLOBBY/GAME: {node.fork=} {node.proto=} {node.data=} {node.hint=}")

                elif ev in [node.USERS]:
                    ...

                elif ev in [node.GLOBAL]:
                    print("GLOBAL:", node.data)

                elif ev in [node.SPURIOUS]:
                    print(f"\nRAW: {node.proto=} {node.data=}")

                elif ev in [node.USERLIST]:
                    print(node.proto, node.users)

                elif ev == node.RAW:
                    print("RAW:", node.data)

                elif ev == node.PING:
                    # print("ping", node.data)
                    ...
                elif ev == node.PONG:
                    # print("pong", node.data)
                    ...

                # promisc mode dumps everything.
                elif ev == node.RX:
                    ...

                else:
                    print(f"52:{ev=} {node.rxq=}")
            except Exception as e:
                print(f"52:{ev=} {node.rxq=} {node.proto=} {node.data=}")
                sys.print_exception(e)

        # TODO Move the following into it's own function soon
        if initializing:
            current_theme.INVERSE_PLAYER_VIEW = not starting_player
            if starting_player:
                pygame.display.set_caption("Chess - White")
            else:
                pygame.display.set_caption("Chess - Black")
            client_game = Game(new_board.copy(), starting_player)
            player = "white" if starting_player else "black"
            opponent = "black" if starting_player else "white"
            game_tab_id = str(node.gid) + "-" + str(node.pid)
            window.sessionStorage.setItem("current_game_id", game_tab_id)
            window.sessionStorage.setItem("draw_request", "false")
            window.sessionStorage.setItem("undo_request", "false")
            web_game_metadata = window.localStorage.getItem("web_game_metadata")
            if web_game_metadata is not None:
                web_game_metadata_dict = json.loads(web_game_metadata)
            else:
                web_game_metadata_dict = {}
            # TODO extend this to load defaults for historic games in script or through browser
            if isinstance(web_game_metadata_dict, dict) or web_game_metadata is None:
                web_game_metadata_dict[game_tab_id] = {
                    "end_state": '',
                    "forced_end": '',
                    "player_color": player,
                    "alg_moves": [],
                    "undo_move": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "undo_move_accept": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "undo_move_deny": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "resign": {
                        "execute": False,
                        "update_executed": False
                    },
                    "draw_offer": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "draw_offer_accept": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "draw_offer_deny": {
                        "execute": False,
                        "update_executed": False,
                        "reset": False
                    },
                    "cycle_theme": {
                        "execute": False,
                        "update_executed": False
                    },
                    "flip_board": {
                        "execute": False,
                        "update_executed": False
                    },
                    "console_messages": []
                }
            else:
                raise Exception("Browser game metadata of wrong type", web_game_metadata_dict)
            web_game_metadata = json.dumps(web_game_metadata_dict)
            window.localStorage.setItem("web_game_metadata", web_game_metadata)

            initializing, initialized = False, True
            node.tx({node.CMD: f"{player} initialized"})
        elif not initialized:
            starting_player = True
            current_theme.INVERSE_PLAYER_VIEW = not starting_player
            pygame.display.set_caption("Chess - Waiting on Connection")
            client_game = Game(new_board.copy(), starting_player)
            player = "white"
            opponent = "black"

        # TODO move into it's own function
        if waiting:
            # Need to pump the event queque like below in order to move window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    waiting = False

            # Clear the screen
            game_window.fill((0, 0, 0))

            # Draw the board
            draw_board({
                'window': game_window,
                'theme': current_theme,
                'board': client_game.board,
                'chessboard': drawing_settings["chessboard"],
                'selected_piece': selected_piece,
                'current_position': client_game.current_position,
                'previous_position': client_game.previous_position,
                'right_clicked_squares': right_clicked_squares,
                'coordinate_surface': drawing_settings["coordinate_surface"],
                'drawn_arrows': drawn_arrows,
                'starting_player': client_game._starting_player,
                'valid_moves': valid_moves,
                'valid_captures': valid_captures,
                'valid_specials': valid_specials,
                'pieces': pieces,
                'hovered_square': hovered_square,
                'selected_piece_image': selected_piece_image
            })

            # Darken the screen
            overlay = pygame.Surface((current_theme.WIDTH, current_theme.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))

            # Blit the overlay surface onto the main window
            game_window.blit(overlay, (0, 0))
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        # Web browser actions/commands are received in previous loop iterations
        # Need to make it dry
        if client_state_actions["undo"] and not client_state_actions["undo_sent"]:
            offer_data = {node.CMD: "undo_offer"}
            node.tx(offer_data, shm=True)
            client_state_actions["undo_sent"] = True
        if client_state_actions["undo_accept"] and client_state_actions["undo_received"]:
            # This initial section should be a bespoke function
            # The sender will sync no need to apply again
            offer_data = {node.CMD: "undo_accept"}
            node.tx(offer_data, shm=True)
            your_turn = client_game.current_turn == client_game._starting_player
            client_game.undo_move()
            if not your_turn:
                client_game.undo_move()
            sent = 0
            window.sessionStorage.setItem("undo_request", "false")
            hovered_square = None
            selected_piece_image = None
            selected_piece = None
            first_intent = False
            valid_moves, valid_captures, valid_specials = [], [], []
            right_clicked_squares = []
            drawn_arrows = []
            # The below can all be added to a DRY function
            client_state_actions["undo_received"] = False
            client_state_actions["undo_accept"] = False
            client_state_actions["undo_accept_executed"] = True
        if client_state_actions["undo_response_received"]:
            client_state_actions["undo_sent"] = False
            client_state_actions["undo_response_received"] = False
            client_state_actions["undo"] = False
            client_state_actions["undo_executed"] = True
        if client_state_actions["undo_deny"]:
            reset_data = {node.CMD: "reset"}
            node.tx(reset_data, shm=True)
            client_state_actions["undo_deny"] = False
            client_state_actions["undo_deny_executed"] = True
            client_state_actions["undo_received"] = False
            window.sessionStorage.setItem("undo_request", "false")

        if client_state_actions["resign"]:
            client_game.forced_end = "White Resigned" if client_game.current_turn else "Black Resigned"
            print(client_game.forced_end)
            running = False
            client_game.end_position = True
            client_game.add_end_game_notation(True)
            client_state_actions["resign"] = False
            client_state_actions["resign_executed"] = True

        if client_state_actions["draw_offer"] and not client_state_actions["draw_offer_sent"]:
            offer_data = {node.CMD: "draw_offer"}
            node.tx(offer_data, shm=True)
            client_state_actions["draw_offer_sent"] = True
        if client_state_actions["draw_response_received"]:
            client_game.forced_end = "Draw by mutual agreement"
            print(client_game.forced_end)
            running = False
            client_game.end_position = True
            client_game.add_end_game_notation(False)
            client_state_actions["draw_offer_sent"] = False
            client_state_actions["draw_response_received"] = False
            client_state_actions["draw_offer"] = False
            client_state_actions["draw_offer_executed"] = True
        if client_state_actions["draw_accept"] and client_state_actions["draw_offer_received"]:
            offer_data = {node.CMD: "draw_accept"}
            node.tx(offer_data, shm=True)
            client_game.forced_end = "Draw by mutual agreement"
            print(client_game.forced_end)
            running = False
            client_game.end_position = True
            client_game.add_end_game_notation(False)
            client_state_actions["draw_offer_received"] = False
            client_state_actions["draw_accept"] = False
            client_state_actions["draw_accept_executed"] = True
        if client_state_actions["draw_deny"]:
            reset_data = {node.CMD: "reset"}
            node.tx(reset_data, shm=True)
            client_state_actions["draw_deny"] = False
            client_state_actions["draw_deny_executed"] = True
            client_state_actions["draw_offer_received"] = False
            window.sessionStorage.setItem("draw_request", "false")

        # Theme cycle
        if client_state_actions["cycle_theme"]:
            drawing_settings["theme_index"] += 1
            drawing_settings["theme_index"] %= len(themes)
            current_theme.apply_theme(themes[drawing_settings["theme_index"]])
            # Redraw board and coordinates
            drawing_settings["chessboard"] = generate_chessboard(current_theme)
            drawing_settings["coordinate_surface"] = generate_coordinate_surface(current_theme)
            client_state_actions["cycle_theme"] = False
            client_state_actions["cycle_theme_executed"] = True

        if client_state_actions["flip"]:
            current_theme.INVERSE_PLAYER_VIEW = not current_theme.INVERSE_PLAYER_VIEW
            # Redraw board and coordinates
            drawing_settings["chessboard"] = generate_chessboard(current_theme)
            drawing_settings["coordinate_surface"] = generate_coordinate_surface(current_theme)
            client_state_actions["flip"] = False
            client_state_actions["flip_executed"] = True

        # An ugly indent but we need to send the draw_offer and resign execution status and skip unnecessary events
        # TODO make this skip cleaner or move it into a function
        if not client_game.end_position:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        left_mouse_button_down = True
                    if event.button == 3:
                        right_mouse_button_down = True
                    
                    if right_mouse_button_down:
                        # If a piece is selected, unselect them and do not execute move logic
                        hovered_square = None
                        selected_piece_image = None
                        selected_piece = None
                        first_intent = False
                        valid_moves, valid_captures, valid_specials = [], [], []
                        
                        x, y = pygame.mouse.get_pos()
                        row, col = get_board_coordinates(x, y, current_theme.GRID_SIZE)
                        # Change input to reversed board given inverse view
                        if current_theme.INVERSE_PLAYER_VIEW:
                            row, col = map_to_reversed_board(row, col)
                        if not left_mouse_button_down:
                            current_right_clicked_square = (row, col)
                        continue

                    if left_mouse_button_down:
                        # Clear highlights and arrows
                        right_clicked_squares = []
                        drawn_arrows = []

                        x, y = pygame.mouse.get_pos()
                        row, col = get_board_coordinates(x, y, current_theme.GRID_SIZE)
                        # Change input to reversed board given inverse view
                        if current_theme.INVERSE_PLAYER_VIEW:
                            row, col = map_to_reversed_board(row, col)
                        piece = client_game.board[row][col]
                        is_white = piece.isupper()
                        
                        if not selected_piece:
                            if piece != ' ':
                                # Update states with new piece selection
                                first_intent, selected_piece, selected_piece_image, valid_moves, valid_captures, valid_specials, hovered_square = \
                                    handle_new_piece_selection(client_game, row, col, is_white, hovered_square)
                                
                        else:
                            if client_game.current_turn == client_game._starting_player:
                                ## Free moves or captures
                                if (row, col) in valid_moves:
                                    promotion_square, promotion_required = \
                                        handle_piece_move(client_game, selected_piece, row, col, valid_captures)
                                    
                                    # Clear valid moves so it doesn't re-enter the loop and potentially replace the square with an empty piece
                                    valid_moves, valid_captures, valid_specials = [], [], []
                                    # Reset selected piece variables to represent state
                                    selected_piece, selected_piece_image = None, None
                                    
                                    if client_game.end_position:
                                        running = False
                                        break
                                
                                ## Specials
                                elif (row, col) in valid_specials:
                                    piece, is_white = handle_piece_special_move(client_game, selected_piece, row, col)
                                    
                                    # Clear valid moves so it doesn't re-enter the loop and potentially replace the square with an empty piece
                                    valid_moves, valid_captures, valid_specials = [], [], []
                                    # Reset selected piece variables to represent state
                                    selected_piece, selected_piece_image = None, None

                                    if client_game.end_position:
                                        running = False
                                        break

                                else:
                                    # Otherwise we are considering another piece or a re-selected piece
                                    if piece != ' ':
                                        if (row, col) == selected_piece:
                                            # If the mouse stays on a square and a piece is clicked a second time 
                                            # this ensures that mouseup on this square deselects the piece
                                            if first_intent:
                                                first_intent = False
                                            # Redraw the transparent dragged piece on subsequent clicks
                                            selected_piece_image = transparent_pieces[piece]
                                        
                                        if (row, col) != selected_piece:
                                            first_intent, selected_piece, selected_piece_image, valid_moves, valid_captures, valid_specials, hovered_square = \
                                                handle_new_piece_selection(client_game, row, col, is_white, hovered_square)
                            
                            # Otherwise (when not our move) we are considering another piece or a re-selected piece
                            elif piece != ' ':
                                if (row, col) == selected_piece:
                                    # If the mouse stays on a square and a piece is clicked a second time 
                                    # this ensures that mouseup on this square deselects the piece
                                    if first_intent:
                                        first_intent = False
                                    # Redraw the transparent dragged piece on subsequent clicks
                                    selected_piece_image = transparent_pieces[piece]
                                
                                if (row, col) != selected_piece:
                                    first_intent, selected_piece, selected_piece_image, valid_moves, valid_captures, valid_specials, hovered_square = \
                                        handle_new_piece_selection(client_game, row, col, is_white, hovered_square)    

                elif event.type == pygame.MOUSEMOTION:
                    x, y = pygame.mouse.get_pos()
                    row, col = get_board_coordinates(x, y, current_theme.GRID_SIZE)
                    if current_theme.INVERSE_PLAYER_VIEW:
                        row, col = map_to_reversed_board(row, col)

                    # Draw new hover with a selected piece and LMB
                    if left_mouse_button_down and selected_piece is not None:  
                        if (row, col) != hovered_square:
                            hovered_square = (row, col)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        left_mouse_button_down = False
                        hovered_square = None
                        selected_piece_image = None
                        # For the second time a mouseup occurs on the same square it deselects it
                        # This can be an arbitrary number of mousedowns later
                        if not first_intent and (row, col) == selected_piece:
                                selected_piece = None
                                valid_moves, valid_captures, valid_specials = [], [], []
                        
                        # First intent changed to false if mouseup on same square the first time
                        if first_intent and (row, col) == selected_piece:
                            first_intent = not first_intent
                        
                        if client_game.current_turn == client_game._starting_player:
                            ## Free moves or captures
                            if (row, col) in valid_moves:
                                promotion_square, promotion_required = \
                                    handle_piece_move(client_game, selected_piece, row, col, valid_captures)
                                
                                # Clear valid moves so it doesn't re-enter the loop and potentially replace the square with an empty piece
                                valid_moves, valid_captures, valid_specials = [], [], []
                                # Reset selected piece variables to represent state
                                selected_piece, selected_piece_image = None, None

                                if client_game.end_position:
                                    running = False
                                    break

                            ## Specials
                            elif (row, col) in valid_specials:
                                piece, is_white = handle_piece_special_move(client_game, selected_piece, row, col)
                                
                                # Clear valid moves so it doesn't re-enter the loop and potentially replace the square with an empty piece
                                valid_moves, valid_captures, valid_specials = [], [], []
                                # Reset selected piece variables to represent state
                                selected_piece, selected_piece_image = None, None

                                if client_game.end_position:
                                    running = False
                                    break

                    if event.button == 3:
                        right_mouse_button_down = False
                        # Highlighting individual squares at will
                        if (row, col) == current_right_clicked_square:
                            if (row, col) not in right_clicked_squares:
                                right_clicked_squares.append((row, col))
                            else:
                                right_clicked_squares.remove((row, col))
                        elif current_right_clicked_square is not None:
                            x, y = pygame.mouse.get_pos()
                            row, col = get_board_coordinates(x, y, current_theme.GRID_SIZE)
                            if current_theme.INVERSE_PLAYER_VIEW:
                                row, col = map_to_reversed_board(row, col)
                            end_right_released_square = (row, col)

                            if [current_right_clicked_square, end_right_released_square] not in drawn_arrows:
                                # Disallow out of bound arrows
                                if 0 <= end_right_released_square[0] < 8 and 0 <= end_right_released_square[1] < 8:
                                    drawn_arrows.append([current_right_clicked_square, end_right_released_square])
                            else:
                                drawn_arrows.remove([current_right_clicked_square, end_right_released_square])

        # Clear the screen
        game_window.fill((0, 0, 0))

        # Draw the board
        draw_board({
            'window': game_window,
            'theme': current_theme,
            'board': client_game.board,
            'chessboard': drawing_settings["chessboard"],
            'selected_piece': selected_piece,
            'current_position': client_game.current_position,
            'previous_position': client_game.previous_position,
            'right_clicked_squares': right_clicked_squares,
            'coordinate_surface': drawing_settings["coordinate_surface"],
            'drawn_arrows': drawn_arrows,
            'starting_player': client_game._starting_player,
            'valid_moves': valid_moves,
            'valid_captures': valid_captures,
            'valid_specials': valid_specials,
            'pieces': pieces,
            'hovered_square': hovered_square,
            'selected_piece_image': selected_piece_image
        })

        # Pawn Promotion
        if promotion_required:
            # Lock the game state (disable other input)
            
            # Display an overlay or popup with promotion options
            draw_board_params = {
                'window': game_window,
                'theme': current_theme,
                'board': client_game.board,
                'chessboard': drawing_settings["chessboard"],
                'selected_piece': selected_piece,
                'current_position': client_game.current_position,
                'previous_position': client_game.previous_position,
                'right_clicked_squares': right_clicked_squares,
                'coordinate_surface': drawing_settings["coordinate_surface"],
                'drawn_arrows': drawn_arrows,
                'starting_player': client_game._starting_player,
                'valid_moves': valid_moves,
                'valid_captures': valid_captures,
                'valid_specials': valid_specials,
                'pieces': pieces,
                'hovered_square': hovered_square,
                'selected_piece_image': selected_piece_image
            }

            game_tab_id = str(node.gid) + "-" + str(node.pid)
            promoted, end_state = await promotion_state(
                promotion_square, 
                client_game, 
                row, 
                col, 
                draw_board_params, 
                client_state_actions, 
                command_status_names, 
                drawing_settings, 
                game_tab_id
            )
            promotion_required, promotion_square = False, None

            if promoted:
                hovered_square = None
                selected_piece_image = None
                selected_piece = None
                first_intent = False
                valid_moves, valid_captures, valid_specials = [], [], []
                right_clicked_squares = []
                drawn_arrows = []
                
            if client_game.end_position:
                running = False
                client_game.add_end_game_notation(end_state)

            # Remove the overlay and buttons by redrawing the board
            game_window.fill((0, 0, 0))
            # We likely need to reinput the arguments and can't use the above params as they are updated.
            draw_board({
                'window': game_window,
                'theme': current_theme,
                'board': client_game.board,
                'chessboard': drawing_settings["chessboard"],
                'selected_piece': selected_piece,
                'current_position': client_game.current_position,
                'previous_position': client_game.previous_position,
                'right_clicked_squares': right_clicked_squares,
                'coordinate_surface': drawing_settings["coordinate_surface"],
                'drawn_arrows': drawn_arrows,
                'starting_player': client_game._starting_player,
                'valid_moves': valid_moves,
                'valid_captures': valid_captures,
                'valid_specials': valid_specials,
                'pieces': pieces,
                'hovered_square': hovered_square,
                'selected_piece_image': selected_piece_image
            })
            # On MOUSEDOWN, piece could become whatever was there before and have the wrong color
            # We need to set the piece to be the pawn/new_piece to confirm checkmate immediately 
            # In the case of an undo this is fine and checkmate is always false
            piece = client_game.board[row][col]
            is_white = piece.isupper()

            checkmate, remaining_moves = is_checkmate_or_stalemate(client_game.board, not is_white, client_game.moves)
            if checkmate:
                print("CHECKMATE")
                running = False
                client_game.end_position = True
                client_game.add_end_game_notation(checkmate)
            elif remaining_moves == 0:
                print("STALEMATE")
                running = False
                client_game.end_position = True
                client_game.add_end_game_notation(checkmate)
            # This seems redundant as promotions should lead to unique boards but we leave it in anyway
            elif client_game.threefold_check():
                print("STALEMATE BY THREEFOLD REPETITION")
                client_game.forced_end = "Stalemate by Threefold Repetition"
                running = False
                client_game.end_position = True
                client_game.add_end_game_notation(checkmate)
        
        # Only allow for retrieval of algebraic notation at this point after potential promotion, if necessary in the future
        web_game_metadata = window.localStorage.getItem("web_game_metadata")

        web_game_metadata_dict = json.loads(web_game_metadata)
        game_tab_id = str(node.gid) + "-" + str(node.pid)

        # DEV logs to console
        # web_game_metadata_dict[game_tab_id]['console_messages'] = console_log_messages
        
        # TODO Can just put this into an asynchronous loop if I wanted or needed, can also speed up by only executing with true values
        # Undo move, resign, draw offer, cycle theme, flip command handle
        for status_names in command_status_names:
            handle_command(status_names, client_state_actions, web_game_metadata_dict, "web_game_metadata", game_tab_id)        

        if web_game_metadata_dict[game_tab_id]['alg_moves'] != client_game.alg_moves:
            web_game_metadata_dict[game_tab_id]['alg_moves'] = client_game.alg_moves

            web_game_metadata = json.dumps(web_game_metadata_dict)
            window.localStorage.setItem("web_game_metadata", web_game_metadata)
        
        # Maybe I just set this initially in a better/DRY way, this looks clunky
        # The following just sets web information so that we know the playing player side, it might be useless? Can't remember why I implemented this
        if client_game._starting_player and web_game_metadata_dict[game_tab_id]['player_color'] != 'white':
            web_game_metadata_dict[game_tab_id]['player_color'] = 'white'

            web_game_metadata = json.dumps(web_game_metadata_dict)
            window.localStorage.setItem("web_game_metadata", web_game_metadata)
        elif not client_game._starting_player and web_game_metadata_dict[game_tab_id]['player_color'] != 'black':
            web_game_metadata_dict[game_tab_id]['player_color'] = 'black'

            web_game_metadata = json.dumps(web_game_metadata_dict)
            window.localStorage.setItem("web_game_metadata", web_game_metadata)
        
        try:
            if (client_game.current_turn != client_game._starting_player or not client_game._sync) and not client_game.end_position:
                txdata = {node.CMD: f"{player}_update"}
                if not client_game._sync:
                    txdata[node.CMD] += "_req_sync"
                send_game = client_game.to_json()
                txdata.update({"game": send_game})
                draw_request_value = window.sessionStorage.getItem("draw_request")
                draw_request_value = json.loads(draw_request_value) # TODO Handle invalid case due to altering wherever, not just here also just have a loop here over offers or something
                if not sent and draw_request_value:
                    reset_data = {node.CMD: "reset"}
                    node.tx(reset_data, shm=True)
                    window.sessionStorage.setItem("draw_request", "false")
                    client_state_actions["draw_accept_reset"] = True
                    client_state_actions["draw_deny_reset"] = True
                    client_state_actions["draw_offer_received"] = False
                if not sent and client_state_actions["draw_offer_sent"]:
                    reset_data = {node.CMD: "reset"}
                    node.tx(reset_data, shm=True)
                    client_state_actions["draw_offer"] = False
                    client_state_actions["draw_offer_reset"] = True
                    client_state_actions["draw_offer_sent"] = False
                # TODO To make DRY with above
                undo_request_value = window.sessionStorage.getItem("undo_request")
                undo_request_value = json.loads(undo_request_value)
                if not sent and undo_request_value:
                    reset_data = {node.CMD: "reset"}
                    node.tx(reset_data, shm=True)
                    window.sessionStorage.setItem("undo_request", "false")
                    client_state_actions["undo_accept_reset"] = True
                    client_state_actions["undo_deny_reset"] = True
                    client_state_actions["undo_received"] = False
                if not sent and client_state_actions["undo_sent"]:
                    reset_data = {node.CMD: "reset"}
                    node.tx(reset_data, shm=True)
                    client_state_actions["undo"] = False
                    client_state_actions["undo_reset"] = True
                    client_state_actions["undo_sent"] = False
                if not sent:
                    node.tx(txdata, shm=True)
                    sent = 1
        except Exception as err:
            running = False
            client_game.end_position = True
            print("Could not send/get games... ", err)
            break

        # Only allow for retrieval of algebraic notation at this point after potential promotion, if necessary in the future
        pygame.display.flip()
        await asyncio.sleep(0)

    if client_game.end_position:
        try:
            reset_data = {node.CMD: "reset"}
            node.tx(reset_data, shm=True)
            window.sessionStorage.setItem("draw_request", "false")
            window.sessionStorage.setItem("undo_request", "false")
            txdata = {node.CMD: f"{player}_update"}
            send_game = client_game.to_json()
            txdata.update({"game": send_game})
            node.tx(txdata, shm=True)
        except Exception as err:
            print("Could not send endgame position... ", err)

    while client_game.end_position:
        # Clear any selected highlights
        right_clicked_squares = []
        drawn_arrows = []
        
        # Clear the screen
        game_window.fill((0, 0, 0))

        # Draw the board
        draw_board({
            'window': game_window,
            'theme': current_theme,
            'board': client_game.board,
            'chessboard': drawing_settings["chessboard"],
            'selected_piece': selected_piece,
            'current_position': client_game.current_position,
            'previous_position': client_game.previous_position,
            'right_clicked_squares': right_clicked_squares,
            'coordinate_surface': drawing_settings["coordinate_surface"],
            'drawn_arrows': drawn_arrows,
            'starting_player': client_game._starting_player,
            'valid_moves': valid_moves,
            'valid_captures': valid_captures,
            'valid_specials': valid_specials,
            'pieces': pieces,
            'hovered_square': hovered_square,
            'selected_piece_image': selected_piece_image
        })

        # Darken the screen
        overlay = pygame.Surface((current_theme.WIDTH, current_theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))

        # Blit the overlay surface onto the main window
        game_window.blit(overlay, (0, 0))
        pygame.display.flip()

        web_game_metadata = window.localStorage.getItem("web_game_metadata")

        web_game_metadata_dict = json.loads(web_game_metadata)

        if web_game_metadata_dict[game_tab_id]['end_state'] != client_game.alg_moves[-1]:
            web_game_metadata_dict[game_tab_id]['end_state'] = client_game.alg_moves[-1]
            web_game_metadata_dict[game_tab_id]['forced_end'] = client_game.forced_end
            web_game_metadata_dict[game_tab_id]['alg_moves'] = client_game.alg_moves

            web_game_metadata = json.dumps(web_game_metadata_dict)
            window.localStorage.setItem("web_game_metadata", web_game_metadata)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client_game.end_position = False
        await asyncio.sleep(0)

    # Quit Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())