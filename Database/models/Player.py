from pony.orm import *
from Database.Database import Player, ROL, GAME_STATE
from Database.exceptions import *
from Game.cards.cards import *
from Database.models.Card import *


# ----- Basic player functions ----- #


@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player_by_name(player_name: str) -> Player:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name)


@db_session
def player_exists(player_name: str) -> bool:
    return Player.exists(player_name=player_name)


@db_session
def is_infected(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["INFECTADO"]


@db_session
def is_human(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["HUMANO"]


@db_session
def is_player_alive(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.is_alive


@db_session
def get_player_position(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return player.position


@db_session
def get_player_match(player_name: str) -> int:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    player = get_player_by_name(player_name)
    if not player.match:
        raise PlayerNotInMatch("El jugador no está en partida")
    return player.match.id


@db_session
def get_player_by_id(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise PlayerNotFound("Jugador no encontrado")
    return Player[player_id]


@db_session
def get_player_id(player_name: str) -> int:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name).id


@db_session
def is_in_match(player_name: str, match_id: int) -> bool:
    match = get_player_match(player_name)
    return match == match_id


@db_session
def is_host(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.is_host


@db_session
def set_player_alive(player_name: str, alive: bool):
    player = get_player_by_name(player_name)
    player.is_alive = alive


@db_session
def get_player_alive(player_id: int) -> bool:
    player = get_player_by_id(player_id)
    return player.is_alive


@db_session
def is_lacosa(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["LA_COSA"]


@db_session
def is_in_quarantine(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.in_quarantine


@db_session
def infect_player(player_name: str):
    player = get_player_by_name(player_name)
    player.rol = ROL["INFECTADO"]
    player.match.last_infected = player_name


def get_role_name(rol: int) -> str:
    return _get_first_ocurrence(ROL, rol)


def _get_first_ocurrence(dic: dict, value: int) -> str:
    for key in dic:
        if dic[key] == value:
            return key


def get_state_name(state: int) -> str:
    return _get_first_ocurrence(GAME_STATE, state)


# ---- Player functions with cards ---- #


@db_session
def get_cards(player: Player) -> list:
    deck_data = []
    for card in player.cards:
        deck_data.append(
            {
                "card_id": card.id,
                "card_name": card.card_name,
                "type": card.type,
            }
        )
    return sorted(deck_data, key=lambda d: d["card_id"])


@db_session
def get_player_hand(player_name: str) -> list:
    player = get_player_by_name(player_name)
    return get_cards(player)


@db_session
def get_random_card_from(player_name: str) -> str:
    player = get_player_by_name(player_name)
    card = list(player.cards.random(1))[0]
    return card.card_name


@db_session
def get_player_cards_names(player_name: str) -> list:
    player = get_player_by_name(player_name)
    return [c.card_name for c in player.cards]


@db_session
def has_card(player_name, card_id):
    player = Player.get(player_name=player_name)
    card = Card.get(id=card_id)
    return card in player.cards


@db_session
def count_infection_cards(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return player.cards.filter(lambda c: c.type == CardType.CONTAGIO.value).count()


@db_session
def exchange_players_cards(player1: str, card1: int, player2: str, card2: int):
    player1 = get_player_by_name(player1)
    player2 = get_player_by_name(player2)
    card1 = get_card_by_id(card1)
    card2 = get_card_by_id(card2)

    player1.cards.remove(card1)
    player2.cards.remove(card2)
    card1.player.remove(player1)
    card2.player.remove(player2)

    player1.cards.add(card2)
    player2.cards.add(card1)
    card1.player.add(player2)
    card2.player.add(player1)
