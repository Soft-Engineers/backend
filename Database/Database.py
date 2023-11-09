from pony.orm import *
import sys
from datetime import *

db = pony.orm.Database()


if "pytest" in sys.modules or "unittest" in sys.modules:
    db.bind(provider="sqlite", filename=":sharedmemory:")
else:
    db.bind(provider="sqlite", filename="lacosa.sqlite", create_db=True)


class Match(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    password = Optional(str, default="")
    min_players = Required(int)
    max_players = Required(int)
    players = Set("Player")
    initiated = Optional(bool, default=False)
    clockwise = Optional(bool, default=True)
    current_player = Required(int, default=0)
    deck = Set("Deck")
    game_state = Optional(int, default=0)
    played_card = Optional(int, default=None, nullable=True)
    turn_player = Optional(str, default=None, nullable=True)
    target_player = Optional(str, default=None, nullable=True)
    exchange_card = Optional(int, default=None, nullable=True)
    exchange_player = Optional(str, default=None, nullable=True)
    last_infected = Optional(str, default=None, nullable=True)
    obstacles = Optional(IntArray, default=[])
    timestamp = Optional(float, default=None, nullable=True)
    chat_record = Optional(StrArray, default=[])
    logs_record = Optional(StrArray, default=[])


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)  # 0: default, 1: human, 2: la cosa, 3: infected
    is_alive = Optional(bool)
    in_game = Optional(bool, default=False)
    in_quarantine = Optional(int, default=0)


class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    number = Optional(int)
    card_name = Required(str)
    type = Required(int)
    player = Set(Player)
    deck = Set("Deck")


class Deck(db.Entity):
    match = Required(Match)
    cards = Set(Card)
    is_discard = Required(bool)
    PrimaryKey(match, is_discard)


db.generate_mapping(create_tables=True)


# --- Constants --- #

ROL = {"HUMANO": 1, "LA_COSA": 2, "INFECTADO": 3}
GAME_STATE = {
    "DRAW_CARD": 1,
    "PLAY_TURN": 2,
    "FINISHED": 3,
    "EXCHANGE": 4,
    "WAIT_EXCHANGE": 5,
    "WAIT_DEFENSE": 6,
    "PANIC": 7,
    "REVELACIONES": 9,
    "DISCARD": 10,
}
