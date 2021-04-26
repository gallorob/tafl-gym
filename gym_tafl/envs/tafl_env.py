import gym
from gym import spaces, logger
from gym.utils import seeding

from gym_tafl.envs._game_engine import *
from gym_tafl.envs._utils import *
from gym_tafl.envs.configs import *


class TaflEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 25
    }

    def __init__(self):
        """
        Create the environment
        """
        # game variables
        self.variant = 'tablut'
        self.game_engine = GameEngine(self.variant)
        self.n_rows = self.game_engine.n_rows
        self.n_cols = self.game_engine.n_cols
        self.board = np.zeros((self.n_rows, self.n_cols))
        self.player = self.game_engine.STARTING_PLAYER
        self.last_moves: List[Tuple[int, int, int, int]] = []
        self.n_moves = 0
        # environment variables
        # from(row, col) -> to(row, col)
        self.action_space = None
        self.valid_actions = None
        self.observation_space = None
        self.done = False
        self.steps_beyond_done = None
        self.viewer = None
        self.np_random = seeding.np_random(0)
        # location independent assets directory
        self.assets = {}
        self.square_width = 0
        self.square_height = 0

    def step(self, action: int) -> Tuple[np.ndarray, int, bool, dict]:
        """
        Apply a single step in the environment using the given action

        :param action: The action to apply
        """
        assert self.action_space.contains(action), f"[ERR: step] Unrecognized action: {action}"
        assert action in self.valid_actions, f"[ERR: step] Invalid action: {action}"

        info = {}  # TODO: Info should be handled by game engine
        if self.done:
            logger.warn('Stop calling `step()` after the episode is done! Use `reset()`')
            reward = 0
        else:
            move = decimal_to_space(action, self.board.shape[0], self.board.shape[1])
            res = self.game_engine.apply_move(self.board, move)
            move_str = res.get('move')
            info['move'] = move_str
            reward = res.get('reward')
            logger.debug(
                f"[{str(self.n_moves + 1).zfill(int(np.log10(self.game_engine.MAX_MOVES)) + 1)}/{self.game_engine.MAX_MOVES + 1}] "
                f"{'ATK' if self.player == ATK else 'DEF'} : {move_str}")
            if res.get('game_over', False):
                self.done = True
                info = {
                    'winner': self.player,
                    'reason': 'King escaped' if self.player == DEF else 'King was captured',
                    'move': move_str
                }
            else:
                res = self.game_engine.check_endgame(last_moves=self.last_moves,
                                                     last_move=move,
                                                     player=self.player,
                                                     n_moves=self.n_moves)
                reward += res.get('reward')
                if res.get('game_over', False):
                    self.done = True
                    info = {
                        'winner': res.get('winner'),
                        'reason': res.get('reason'),
                        'move': move_str
                    }
                else:
                    # update moves short-term history
                    if len(self.last_moves) == 8:
                        self.last_moves.pop(0)
                    self.last_moves.append(move)

                    # update the action space
                    self.player = ATK if self.player == DEF else DEF
                    self.valid_actions = self.game_engine.legal_moves(self.board, self.player)

                    # no moves for the opponent check
                    if len(self.valid_actions) == 0:
                        self.done = True
                        reward += 100
                        info = {
                            'winner': 'ATK' if self.player == DEF else 'DEF',
                            'reason': 'Opponents has no moves available',
                            'move': move_str
                        }
            if self.done:
                logger.debug(f"Match ended; reason: {info.get('reason')}; "
                             f"Winner: {'ATK' if info.get('winner') == ATK else ('DEF' if info.get('winner') == DEF else 'DRAW')}")
            self.n_moves += 1

        return self.board, reward, self.done, info

    def change_variant(self,
                       variant: str) -> None:
        self.variant = variant
        self.game_engine = GameEngine(self.variant)
        self.reset()

    def reset(self) -> np.array:
        """
        Reset the current scene, computing the observations

        :return: The state observations
        """
        self.done = False
        self.player = self.game_engine.STARTING_PLAYER
        self.n_rows = self.game_engine.n_rows
        self.n_cols = self.game_engine.n_cols
        self.board = np.zeros((self.n_rows, self.n_cols))
        self.game_engine.no_capture_turns_counter = 0
        self.game_engine.fill_board(self.board)
        # initialize action space
        self.valid_actions = self.game_engine.legal_moves(self.board, self.game_engine.STARTING_PLAYER)
        self.action_space = spaces.Discrete(len(IDX_TO_POS.keys()))
        self.last_moves = []
        self.n_moves = 0
        logger.debug('New match started')
        return self.board

    def render(self, mode: str = 'human'):
        """
        Render the current state of the scene

        :param mode: The rendering mode to use
        """
        from gym.envs.classic_control import rendering
        import os

        if self.viewer is None:
            assets_dir = os.path.dirname(__file__)
            assets_dir = os.path.join(assets_dir, 'assets')
            # assets for tiles and background
            self.assets = {
                DEFENDER: os.path.join(assets_dir, 'defender.png'),
                ATTACKER: os.path.join(assets_dir, 'attacker.png'),
                KING: os.path.join(assets_dir, 'king.png'),
                THRONE: os.path.join(assets_dir, 'throne.png'),
                CORNER: os.path.join(assets_dir, 'throne.png'),
            }
            # game & rendering variables
            self.square_width = SCR_WIDTH / (self.n_cols + 1)
            self.square_height = SCR_HEIGHT / (self.n_rows + 1)
            board_colors = [
                tuple(int(BOARD_COLORS[0][i:i + 2], 16) / 255 for i in (0, 2, 4)),
                tuple(int(BOARD_COLORS[1][i:i + 2], 16) / 255 for i in (0, 2, 4))
            ]

            self.viewer = rendering.Viewer(SCR_WIDTH, SCR_HEIGHT)

            # rows numbers and columns letters
            rows = [rendering.Image(fname=os.path.join((os.path.join(assets_dir, 'rows')), str(i) + '.png'),
                                    width=self.square_width,
                                    height=self.square_height) for i in range(self.n_rows)]
            columns = [rendering.Image(fname=os.path.join((os.path.join(assets_dir, 'columns')), str(i) + '.png'),
                                       width=self.square_width,
                                       height=self.square_height) for i in range(self.n_rows)]
            for i, img in enumerate(rows):
                img.set_color(1., 1., 1.)
                img.add_attr(rendering.Transform(translation=(self.square_width / 2,
                                                              i * self.square_height + (3 / 2) * self.square_height)))
                self.viewer.add_geom(img)

            for i, img in enumerate(columns):
                img.set_color(1., 1., 1.)
                img.add_attr(rendering.Transform(translation=(i * self.square_width + (3 / 2) * self.square_width,
                                                              self.square_height / 2)))
                self.viewer.add_geom(img)

            # add the tiles
            c = 0
            for i in range(self.n_rows, 0, -1):
                for j in range(1, self.n_cols + 1):
                    tile = rendering.make_polygon([(i * self.square_width, j * self.square_height),
                                                   ((i + 1) * self.square_width, j * self.square_height),
                                                   ((i + 1) * self.square_width, (j + 1) * self.square_height),
                                                   (i * self.square_width, (j + 1) * self.square_height)])
                    r, g, b = board_colors[c]
                    tile.set_color(r, g, b)
                    c = 1 if c == 0 else 0
                    self.viewer.add_geom(tile)
            # throne
            if not self.game_engine.no_throne:
                throne = rendering.Image(self.assets.get(THRONE), self.square_width, self.square_height)
                throne.set_color(1., 1., 1.)
                throne.add_attr(
                    rendering.Transform(
                        translation=((self.n_cols // 2 + 1) * self.square_width + (self.square_width / 2),
                                     (self.n_rows // 2 + 1) * self.square_height + (self.square_height / 2))))
                self.viewer.add_geom(throne)

        # add pieces as a one-time render
        for i in range(self.board.shape[0]):
            for j in range(self.board.shape[1]):
                p = self.board[i, j]
                if p != EMPTY:
                    r = i + 1
                    c = j + 1
                    tile = rendering.Image(self.assets.get(p), self.square_width, self.square_height)
                    tile.set_color(1., 1., 1.)
                    tile.add_attr(rendering.Transform(translation=(c * self.square_width + (self.square_width / 2),
                                                                   (self.board.shape[
                                                                        0] - r + 1) * self.square_height + (
                                                                           self.square_height / 2))))
                    self.viewer.add_onetime(tile)

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def close(self):
        """
        Terminate the episode
        """
        if self.viewer:
            self.viewer.close()
            self.viewer = None
