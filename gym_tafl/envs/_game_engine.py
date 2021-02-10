import configparser
import os

from gym_tafl.envs._utils import *
from gym_tafl.envs.configs import *


class GameEngine:
    def __init__(self, variant: str):
        self.variant = variant

        variants_dir = os.path.join(os.getcwd(), 'variants')
        variant_file = os.path.join(variants_dir, f'{variant}.ini')
        assert os.path.isfile(variant_file), f"[ERR GameEngine.__init__] Unknown variant {self.variant}"

        variant_config = configparser.ConfigParser()
        variant_config.read(variant_file)

        # tile values
        self.board = variant_config['VARIANT'].get('board').split(',')
        self.GAME_OVER_REWARD = 100
        self.MAX_REWARD = self.GAME_OVER_REWARD
        self.MAX_MOVES = variant_config['VARIANT'].getint('max_moves')

        players = {
            'ATK': ATK,
            'DEF': DEF
        }
        self.piece_reward = {
            KING: 16,
            DEFENDER: 2,
            ATTACKER: -1
        }

        self.info = {}
        self.STARTING_PLAYER = players[variant_config['VARIANT'].get('starting_player')]
        self.n_rows = variant_config['VARIANT'].getint('n_rows')
        self.n_cols = variant_config['VARIANT'].getint('n_cols')
        self.vector_mask = vector_mask

        # rules
        self.draw_after_50_turns_without_capture = variant_config['DRAW CONDITION']\
            .getboolean('draw_after_50_turns_without_capture')
        self.no_capture_turns_counter = 0

        self.edge_escape = variant_config['OBJECTIVE'].getboolean('edge_escape')

        self.no_throne = variant_config['THRONE'].getboolean('no_throne')

        self.unrestricted_movement = variant_config['MOVEMENT'].getboolean('unrestricted_movement')

        if not self.unrestricted_movement:
            self.m_counter = {
                KING: 1 if (variant_config['MOVEMENT'].getboolean('king_only_moves_1_tile') or
                            variant_config['MOVEMENT'].getboolean('all_move_only_1_tile')) else max(self.n_rows,
                                                                                                    self.n_cols),
                ATTACKER: 1 if variant_config['MOVEMENT'].getboolean('all_move_only_1_tile') else max(self.n_rows,
                                                                                                      self.n_cols),
                DEFENDER: 1 if variant_config['MOVEMENT'].getboolean('all_move_only_1_tile') else max(self.n_rows,
                                                                                                      self.n_cols)
            }

        self.pieces_can_jump_over_throne = variant_config['MOVEMENT'].getboolean('pieces_can_jump_over_throne')

    def fill_board(self, board: np.array):
        char_to_tile = {
            'a': ATTACKER,
            'k': KING,
            'd': DEFENDER
        }

        if self.variant == 'tablut':
            assert len(self.board) == board.shape[
                0], f"[ERR GameEngine.fill_board] Unexpected board length: {len(self.board)}"
            for j, row in enumerate(self.board):
                i = 0
                for c in row:
                    assert i < board.shape[1], f"[ERR GameEngine.fill_board] Unexpected row configuration: {row}"
                    if c.isdigit():
                        i += int(c)
                    else:
                        t = char_to_tile[c.lower()]
                        board[j, i] = t
                        self.MAX_REWARD += abs(self.piece_reward.get(t))
                        i += 1

    def legal_moves(self, board: np.array, player: int):
        assert player in [ATK, DEF], f"[ERR: legal_moves] Unrecognized player type: {player}"
        moves = []
        for i in range(board.shape[0]):
            for j in range(board.shape[1]):
                p = board[i, j]
                if p in [KING, ATTACKER, DEFENDER]:
                    if (p == ATTACKER and player == ATK) or \
                            (p != ATTACKER and player == DEF):
                        moves.extend(self._legal_moves(board, p, (i, j)))
        return moves

    def _legal_moves(self,
                     board: np.array,
                     piece: int,
                     position: Tuple[int, int]) -> List[int]:
        """
        Compute the legal and valid moves for the selected piece in the given board

        :param board: The current board
        :param piece: The selected piece
        :param position: The selected piece position
        :return: A list of valid moves for the piece in the given board
        """
        moves = []
        for inc_i, inc_j in DIRECTIONS:
            i, j = position
            c = 0
            while self.unrestricted_movement or c < self.m_counter[piece]:
                i += inc_i
                j += inc_j
                c += 1
                if i < 0 or i > board.shape[0] - 1 or j < 0 or j > board.shape[1] - 1:
                    break
                t_tile = board[i, j]
                if t_tile == EMPTY:
                    moves.append(space_to_decimal(values=(position[0], position[1], i, j),
                                                  rows=board.shape[0],
                                                  cols=board.shape[1]))
                elif t_tile == THRONE:
                    if piece == KING:
                        moves.append(space_to_decimal(values=(position[0], position[1], i, j),
                                                      rows=board.shape[0],
                                                      cols=board.shape[1]))
                    else:
                        if self.pieces_can_jump_over_throne:
                            continue
                        else:
                            break
                else:
                    break
        return moves

    def board_value(self, board: np.array) -> int:
        value = 0
        for i in range(board.shape[0]):
            for j in range(board.shape[1]):
                p = board[i, j]
                # if p == KING:
                #     value += 16
                # elif p == DEFENDER:
                #     value += 2
                # elif p == ATTACKER:
                #     value -= 1
                # else:
                #     continue
                value += self.piece_reward.get(p, 0)
        return value

    def alt_apply_move(self, board: np.ndarray, action: int) -> dict:
        move = decimal_to_space(action, board.shape[0], board.shape[1])
        return self.apply_move(board=board,
                               move=move)

    def apply_move(self, board: np.array, move: Tuple[int, int, int, int]) -> dict:
        fi, fj, ti, tj = move
        assert board[fi, fj] in [KING, ATTACKER, DEFENDER], \
            f"[ERR: apply_move] Selected invalid piece: {position_as_str(position=(fi, fj), rows=board.shape[0])}"
        assert board[ti, tj] not in [KING, ATTACKER, DEFENDER], \
            f"[ERR: apply_move] Invalid destination: {position_as_str(position=(ti, tj), rows=board.shape[0])}"
        info = {
            'game_over': False,
            'move': position_as_str((fi, fj), board.shape[0]).upper() + '-' + position_as_str((ti, tj),
                                                                                              board.shape[0]).upper(),
            'reward': 0
        }
        # update board and piece
        board[ti, tj] = board[fi, fj]
        board[fi, fj] = THRONE if not self.no_throne and on_throne_arr(board, (fi, fj)) else EMPTY
        # check if king has escaped
        if board[ti, tj] == KING and self.edge_escape and on_edge_arr(board, (ti, tj)):
            info['game_over'] = True
            info['reward'] += self.GAME_OVER_REWARD
        elif board[ti, tj] == KING and (not self.edge_escape) and on_corner_arr(board, (ti, tj)):
            info['game_over'] = True
            info['reward'] += self.GAME_OVER_REWARD
        # process captures
        to_remove = self.process_captures(board, (ti, tj))
        if len(to_remove) == 0:
            self.no_capture_turns_counter += 1
        else:
            self.no_capture_turns_counter = 0
        for (i, j) in to_remove:
            if board[i, j] == KING:
                info['game_over'] = True
                info['reward'] += 100
            board[i, j] = THRONE if on_throne_arr(board, (i, j)) else EMPTY
            info['move'] += 'x' + position_as_str((i, j), board.shape[0]).upper()
        info['reward'] += self.board_value(board)
        # normalize rewards in [-1, 1]
        info['reward'] /= self.MAX_REWARD
        return info

    def process_captures(self, board: np.array, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        captures = []
        piece = board[position]
        for inc_i, inc_j in DIRECTIONS:
            i, j = position
            i += inc_i
            j += inc_j

            if not (out_of_board_arr(board, (i, j))):
                middle_piece = board[i, j]
                if middle_piece in [KING, ATTACKER, DEFENDER]:
                    if (piece == DEFENDER and middle_piece == ATTACKER) or \
                            (piece == KING and middle_piece == ATTACKER) or \
                            (piece == ATTACKER and middle_piece == DEFENDER):
                        i += inc_i
                        j += inc_j
                        if not (out_of_board_arr(board, (i, j))):
                            outer_piece = board[i, j]
                            # normal capture
                            if outer_piece in [KING, ATTACKER, DEFENDER] and \
                                    (piece == outer_piece or (piece == DEFENDER and outer_piece == KING)
                                     or (piece == KING and outer_piece == DEFENDER)):
                                captures.append((i - inc_i, j - inc_j))
                            # capture next to throne
                            elif outer_piece == THRONE and (
                                    (piece == ATTACKER and middle_piece == DEFENDER) or
                                    ((piece == DEFENDER or piece == KING) and piece == ATTACKER)):
                                captures.append((i - inc_i, j - inc_j))
                    # capture king
                    elif piece == ATTACKER and middle_piece == KING:
                        # case 1: king is on the throne, need 4 pieces
                        # case 2: king is next to the throne, need 3 pieces
                        if on_throne_arr(board, (i, j)) or next_to_throne_arr(board, (i, j)):
                            if self._check_king(board, (i, j)) == 4:
                                captures.append((i, j))
                        # case 3: king is free roaming
                        else:
                            i += inc_i
                            j += inc_j
                            if not (out_of_board_arr(board, (i, j))):
                                outer_piece = board[i, j]
                                if outer_piece == ATTACKER:
                                    captures.append((i - inc_i, j - inc_j))
        return captures

    @staticmethod
    def _check_king(board: np.array, position: Tuple[int, int]) -> int:
        threats = 0
        for inc_i, inc_j in DIRECTIONS:
            i, j = position
            i += inc_i
            j += inc_j
            if not out_of_board_arr(board, (i, j)):
                p = board[i, j]
                threats += 1 if p in [ATTACKER, THRONE] else 0
        return threats

    def check_endgame(self,
                      last_moves: List[Tuple[int, int, int, int]],
                      last_move: Tuple[int, int, int, int],
                      player: int,
                      n_moves: int) -> dict:
        info = {
            'game_over': False,
            'reason': '',
            'reward': 0,
            'winner': DRAW
        }
        # check moves repetition
        if n_moves == self.MAX_MOVES:
            info['game_over'] = True
            info['reason'] = 'Moves limit reached'
            info['winner'] = ATK if player == DEF else DEF
        # check threefold repetition
        if check_threefold_repetition(last_moves=last_moves,
                                      last_move=last_move):
            info['game_over'] = True
            info['reason'] = 'Threefold repetition'
            info['winner'] = DRAW
        elif self.draw_after_50_turns_without_capture and self.no_capture_turns_counter == 100:  # 2 moves = 1 turn
            info['game_over'] = True
            info['reason'] = '50 turns with no capture'
            info['winner'] = DRAW
        return info
