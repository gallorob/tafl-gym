import configparser
import os

curr_dir = os.getcwd()
config_file = os.path.join(curr_dir, 'configs.ini')

config = configparser.ConfigParser()
config.read(config_file)

# tile values
EMPTY = config['TILES'].getint('empty')
CORNER = config['TILES'].getint('corner')
THRONE = config['TILES'].getint('throne')
KING = config['TILES'].getint('king')
DEFENDER = config['TILES'].getint('defender')
ATTACKER = config['TILES'].getint('attacker')

# enum for current player
DEF = config['PLAYERS'].getint('defender')
ATK = config['PLAYERS'].getint('attacker')
DRAW = config['PLAYERS'].getint('draw')

# graphic stuff
SCR_WIDTH = config['GRAPHIC'].getint('scr_width')
SCR_HEIGHT = config['GRAPHIC'].getint('scr_height')
BOARD_COLORS = config['GRAPHIC'].get('board_colors').split(',')
