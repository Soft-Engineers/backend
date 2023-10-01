from pony.orm import *
import sys
from datetime import *
from pathlib import Path
from Database.exceptions import *


db = pony.orm.Database()

if "pytest" in sys.modules or "unittest" in sys.modules:
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
    current_player = Optional(int, default=0)
    deck = Set("Deck")


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)
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
def get_match_list():
    match_list = Match.select()[:]
    res_list = []
    for match in match_list:
        res_list.append(
            {
                "name": match.name,
                "min_players": match.min_players,
                "max_players": match.max_players,
                "players": match.players.count(),
            }
        )
    return res_list


@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise MatchNotFound("Match not found")
    return Match[match_id]


@db_session
def _get_match_by_name(match_name: str) -> Match:
    if not Match.exists(name=match_name):
        raise MatchNotFound("Match not found")
    return Match.get(name=match_name)


@db_session
def db_get_match_password(match_name: str) -> str:
    match = _get_match_by_name(match_name)
    return match.password


@db_session
def db_match_has_password(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.password != ""


@db_session
def db_is_match_initiated(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.initiated


@db_session
def db_add_player(player_name: str, match_name: str):
    player = _get_player_by_name(player_name)
    match = _get_match_by_name(match_name)
    if player.match:
        raise PlayerAlreadyInMatch("Player already in a match")
    if len(match.players) >= match.max_players:
        raise MatchIsFull("Match is full")

    match.players.add(player)
    player.match = match


@db_session
def db_get_players(match_name: str) -> list[str]:
    """
    Returns the players names from a match
    """
    match = _get_match_by_name(match_name)
    players = []
    for p in match.players:
        players.append(p.player_name)
    return players


@db_session
def _match_exists(match_name):
    return Match.exists(name=match_name)


@db_session
def db_create_match(
    match_name: str, player_name: str, min_players: int, max_players: int
):
    if _match_exists(match_name):
        raise NameNotAvailable("Match name already used")

    creator = get_player_by_name(player_name)

    if creator.match:
        raise PlayerAlreadyInMatch("Player already in a match")

    match = Match(name=match_name, min_players=min_players, max_players=max_players)
    match.players.add(creator)
    creator.match = match
    creator.is_host = True


@db_session
def get_match_by_name(match_name):
    return Match.get(name=match_name)


@db_session
def is_in_match(player_id, match_id):
    players = Match.get(id=match_id).players
    for player in players:
        if player.id == player_id:
            return True
    return False


# ------------ player functions ----------------
@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player_by_name(player_name):
    if not player_exists(player_name):
        raise PlayerNotFound("Player not found")
    return Player.get(player_name=player_name)

@db_session
def _get_player_by_name(player_name: str) -> Player:
    if not Player.exists(player_name=player_name):
        raise PlayerNotFound("Player not found")
    return Player.get(player_name=player_name)

@db_session
def player_exists(player_name):
    return Player.exists(player_name=player_name)


@db_session
def get_player_by_id(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise PlayerNotFound("Player not found")
    return Player[player_id]


@db_session
def get_player_id(player_name):
    if not player_exists(player_name):
        raise PlayerNotFound("Player not found")
    return Player.get(player_name=player_name).id


@db_session
def get_player_match(player: Player) -> Match:
    match = player.match
    if match is None:
        raise PlayerNotInMatch("Player not in a match")
    return match


@db_session
def _get_players_data(match: Match, except_name: str) -> list:
    players = match.players
    players_data = []
    for player in players:
        if not player.player_name == except_name:
            players_data.append(
                {
                    "name": player.player_name,
                    "position": player.position,
                }
            )
    return players_data


@db_session
def _get_cards_data(player: Player) -> list:
    deck_data = []
    for card in player.cards:
        deck_data.append(
            {
                "name": card.name,
                "number": card.number,
            }
        )
    return deck_data


@db_session
def get_match_state(player_name: str) -> dict:
    player = get_player_by_name(player_name)
    match = get_player_match(player)
    players_data = list(_get_players_data(match, player_name))
    cards_data = _get_cards_data(player)
    return {
        "turn": match.current_player,
        "position": player.position,
        "cards": cards_data,
        "alive": player.is_alive,
        "role": player.rol,
        "clockwise": match.clockwise,
        "players": players_data,
    }
