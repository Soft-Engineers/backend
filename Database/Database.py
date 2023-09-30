from pony.orm import *
import sys
from datetime import *
from pathlib import Path


db = pony.orm.Database()

if "pytest" in sys.modules:
    db.bind(provider="sqlite", filename=":sharedmemory:")
else:
    db.bind(provider="sqlite", filename="lacosa.sqlite", create_db=True)

class Match(db.Entity):
    match_name = PrimaryKey(str)
    password = Optional(str, default="")
    min_players = Required(int)
    max_players = Required(int)
    players = Set("Player")
    initiated = Optional(bool, default=False)
    clockwise = Optional(bool, default=True)
    current_player = Optional(int, default=0)
    deck = Set("Deck")


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)  # 0: default, 1: human, 2: la cosa, 3: infected
    is_alive = Optional(bool)


class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    card_name = Required(str)
    type = Required(int)
    description = Required(str)
    number = Required(int)
    player = Optional(Player)
    deck = Optional("Deck")


class Deck(db.Entity):
    match = Required(Match)
    cards = Set(Card)
    is_discard = Required(bool)
    PrimaryKey(match, is_discard)


db.generate_mapping(create_tables=True)

# ------------ player functions ---------------
@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player(player_name):
    return Player.get(player_name=player_name)


@db_session
def player_exists(player_name):
    return Player.exists(player_name=player_name)


@db_session
def get_player_id(player_name):
    return Player.get(player_name=player_name).id
