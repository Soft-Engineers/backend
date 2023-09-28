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
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    password = Optional(str, default="")
    min_players = Required(int)
    max_players = Required(int)
    players = Set("Player")
    initiated = Optional(bool, default=False)
    clockwise = Optional(bool, default=True)
    current_player = Required(int, default=0)
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
    name = Required(str)
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


@db_session
def get_player_id(player_name):
    return Player.get(player_name=player_name).id


# --- Match Functions --- #


@db_session
def get_match_games(match_id):
    return Match[match_id].games


@db_session
def get_match_players(match_id):
    return Match[match_id].players


@db_session
def get_match_max_players(match_id):
    return Match[match_id].max_players


@db_session
def get_match_min_players(match_id):
    return Match[match_id].min_players


@db_session
def get_match_quantity():
    return Match.select().count()


@db_session
def get_match_quantity_player(match_id):
    return Match[match_id].players.count()


@db_session
def get_match_list(name, filter):
    match filter:
        case "available":
            match_list = Match.select(
                lambda m: (not m.initiated) and m.current_player < m.max_players
            )[:]
        case "public":
            match_list = Match.select(
                lambda m: (not m.initiated)
                and m.current_player < m.max_players
                and m.password == ""
            )[:]
        case "private":
            match_list = Match.select(
                lambda m: (not m.initiated)
                and m.current_player < m.max_players
                and m.password != ""
            )[:]
        case "all":
            match_list = Match.select()[:]
        case _:
            return ["no_valid_filter"]
    res_list = []
    for m in match_list:
        participants_list = []
        for p in m.players:
            participants_list.append(p.player_name)
        res_list.append(
            (
                m.name,
                m.min_players,
                m.max_players,
                participants_list,
            )
        )
    return res_list
