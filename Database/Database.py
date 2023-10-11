from pony.orm import *
import sys
from datetime import *
from pathlib import Path
from Database.exceptions import *
from Database.cards import card_templates, amount_cards, CardType
from random import randrange

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

ROL = {"HUMAN": 1, "LA_COSA": 2, "INFECTED": 3}
GAME_STATE = {"DRAW_CARD": 1, "PLAY_TURN": 2, "FINISHED": 3}

# -- Cards Functions -- #


def _register_rep(rep, card):
    for _ in range(rep.amount):
        Card(card_name=card.card_name, number=rep.number, type=card.type.value)


@db_session
def _register_cards():
    Card.select().delete()
    for card in card_templates:
        for rep in card.repetitions:
            _register_rep(rep, card)


@db_session
def _are_cards_registered():
    return Card.select().count() == amount_cards()


# Register Cards
if not _are_cards_registered():
    _register_cards()


@db_session
def _create_deck(match: Match):
    deck = Deck(match=match, is_discard=False)
    disc_deck = Deck(match=match, is_discard=True)
    num_player = match.players.count()

    for card in Card.select():
        if card.number is None or card.number <= num_player:
            deck.cards.add(card)
            card.deck.add(deck)

    match.deck.add(deck)
    match.deck.add(disc_deck)
    deck.match = match
    disc_deck.match = match


@db_session
def _deal_cards(match: Match):
    deck = match.deck.filter(lambda d: not d.is_discard).first()
    required_cards = match.players.count() * 4

    # Repartir según reglas
    deal_deck = list(
        deck.cards.filter(
            lambda c: c.type != CardType.CONTAGIO.value
            and c.type != CardType.PANICO.value
        ).random(required_cards - 1)
    )
    cosa_card = deck.cards.filter(lambda c: c.card_name == "La Cosa").first()
    deal_deck.insert(randrange(len(deal_deck) + 1), cosa_card)

    players = match.players
    for player in players:
        for _ in range(4):
            card = deal_deck.pop()
            player.cards.add(card)  # Otorgar a jugador
            card.player.add(player)
            deck.cards.remove(card)  # Quitar del mazo
            card.deck.remove(deck)


@db_session
def get_card_by_id(card_id: int) -> Card:
    if not Card.exists(id=card_id):
        raise CardNotFound("Carta no encontrada")
    return Card[card_id]


@db_session
def discard_card(player_id: int, card_id: int):
    player = get_player_by_id(player_id)
    card = get_card_by_id(card_id)
    discard_deck = _get_discard_deck(player.match.id)
    player.cards.remove(card)
    card.player.remove(player)
    discard_deck.cards.add(card)
    card.deck.add(discard_deck)


@db_session
def _play_lanzallamas(player: Player, player_target: Player):
    if not is_adyacent(player, player_target):
        raise InvalidCard("No puedes jugar Lanzallamas a ese jugador")
    player_target.is_alive = False


@db_session
def play_card_from_hand(player_id: int, card_id: int, target_id: int = None):
    card = get_card_by_id(card_id)
    player = get_player_by_id(player_id)
    if target_id is not None:
        player_target = get_player_by_id(target_id)
    if not card in player.cards:
        raise InvalidCard("No tienes esa carta en tu mano")

    if card.card_name == "La Cosa":
        raise InvalidCard("No puedes jugar la carta La Cosa")
    elif card.type == CardType.CONTAGIO.value:
        raise InvalidCard("No puedes jugar la carta ¡Infectado!")

    if card.card_name == "Lanzallamas":
        if target_id is None:
            raise InvalidCard("Lanzallamas requiere un objetivo")
        _play_lanzallamas(player, player_target)
    else:
        pass

    discard_card(player_id, card_id)


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
        raise MatchNotFound("Partida no encontrada")
    return Match[match_id]


@db_session
def _get_match_by_name(match_name: str) -> Match:
    if not Match.exists(name=match_name):
        raise MatchNotFound("Partida no encontrada")
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
        raise PlayerAlreadyInMatch("Jugador ya está en partida")
    if len(match.players) >= match.max_players:
        raise MatchIsFull("La partida está completa")

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
def check_match_existence(match_id):
    return Match.exists(id=match_id)


@db_session
def get_match_info(match_id):
    match = Match[match_id]
    return {
        "name": match.name,
        "min_players": match.min_players,
        "max_players": match.max_players,
        "players": match.players.count(),
    }


@db_session
def db_create_match(
    match_name: str, player_name: str, min_players: int, max_players: int
):
    if _match_exists(match_name):
        raise NameNotAvailable("Nombre de partida ya utilizado")

    creator = get_player_by_name(player_name)

    if creator.match:
        raise PlayerAlreadyInMatch("Jugador ya está en partida")

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


@db_session
def get_match_id(match_name):
    if not _match_exists(match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name).id


@db_session
def db_get_player_match_id(player_name: str):
    if not player_exists(player_name):
        raise PlayerNotFound("Player not found")

    match = Player.get(player_name=player_name).match

    if match is None:
        raise PlayerNotInMatch("Player not in match")

    return match.id


@db_session
def get_match_id_or_None(match_name):
    if not _match_exists(match_name):
        return None
    return Match.get(name=match_name).id


@db_session
def started_match(match_name):
    match = Match.get(name=match_name)
    match.initiated = True
    match.current_player = 1
    position = 0
    # create deck and deal cards
    _create_deck(match)
    _deal_cards(match)
    for player in match.players:
        player.in_game = True
        player.is_alive = True
        player.position = position + 1
        position += 1
        if player.cards.select(lambda c: c.card_name == "La Cosa").first():
            player.rol = 2  # La Cosa
        else:
            player.rol = 1

    return match


@db_session
def get_game_state(match_id: int) -> int:
    return Match[match_id].game_state


@db_session
def set_game_state(match_id: int, state: int):
    match = Match[match_id]
    match.game_state = state


@db_session
def get_match_id(match_name):
    if not _match_exists(match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name).id


@db_session
def get_player_by_position(match_id: int, position: int) -> Player:
    match = _get_match(match_id)
    return match.players.filter(lambda p: p.position == position).first()


@db_session
def get_next_player(match_id: int, start: int) -> int:
    match = _get_match(match_id)
    current_player = start
    total_players = match.players.count()
    direction = 1 if match.clockwise else -1

    while True:
        current_player = (current_player + direction) % total_players
        player = get_player_by_position(match_id, current_player)
        if player.is_alive:
            return current_player


@db_session
def get_previous_player(match_id: int, start: int) -> int:
    match = _get_match(match_id)
    current_player = start
    total_players = match.players.count()
    direction = 1 if match.clockwise else -1

    while True:
        current_player = (current_player - direction) % total_players
        player = get_player_by_position(match_id, current_player)
        if player.is_alive:
            return current_player


@db_session
def set_next_turn(match_id: int):
    match = _get_match(match_id)
    match.current_player = get_next_player(match_id, match.current_player)


@db_session
def get_player_in_turn(match_id: int) -> str:
    match = _get_match(match_id)
    for player in match.players:
        if player.position == match.current_player:
            return player.player_name


@db_session
def check_win_condition(match_id: int) -> bool:
    return check_one_player_alive(match_id) or not is_la_cosa_alive(match_id)


@db_session
def check_one_player_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    alive_players = match.players.filter(lambda p: p.is_alive).count()
    return alive_players == 1


@db_session
def is_la_cosa_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    cosa = match.players.filter(lambda p: p.rol == ROL["LA_COSA"]).first()
    return cosa.is_alive


@db_session
def get_winners(match_id: int) -> list[str]:
    match = _get_match(match_id)
    winners = []
    for player in match.players:
        if player.is_alive:
            winners.append(player.player_name)
    return winners


# ------------ player functions ----------------


@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player_by_name(player_name):
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name)


@db_session
def _get_player_by_name(player_name: str) -> Player:
    if not Player.exists(player_name=player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name)


@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise MatchNotFound("Match not found")
    return Match[match_id]


@db_session
def get_match_turn(match_id: int) -> int:
    match = _get_match(match_id)
    return match.current_player


@db_session
def is_player_alive(player_id: int) -> bool:
    player = get_player_by_id(player_id)
    return player.is_alive


@db_session
def is_player_turn(player_id: int) -> bool:
    player = get_player_by_id(player_id)
    match_id = get_player_match(player_id)
    turn = get_match_turn(match_id)
    return player.position == turn


@db_session
def get_player_position(player_id: int) -> int:
    player = get_player_by_id(player_id)
    return player.position


@db_session
def is_deck_empty(match_id: int) -> bool:
    deck = _get_deck(match_id)
    return len(deck.cards) == 0


@db_session
def get_player_match(player_id: int) -> int:
    player = get_player_by_id(player_id)
    if not player.match:
        raise PlayerNotInMatch("Player not in a match")
    return player.match.id


@db_session
def player_exists(player_name):
    return Player.exists(player_name=player_name)


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
def get_player_hand(player_id: int) -> list[Card]:
    player = get_player_by_id(player_id)
    return list(player.cards)


@db_session
def set_player_alive(player_id: int, alive: bool):
    player = get_player_by_id(player_id)
    player.is_alive = alive


@db_session
def get_player_alive(player_id: int) -> bool:
    player = get_player_by_id(player_id)
    return player.is_alive


@db_session
def is_adyacent(player: Player, player_target: Player) -> bool:
    is_next = (
        get_next_player(player.match.id, player.position) == player_target.position
    )
    is_previous = (
        get_previous_player(player.match.id, player.position) == player_target.position
    )
    return is_next or is_previous


def get_match_locations(match_id: int) -> list:
    match = _get_match(match_id)
    locations = []
    for player in match.players:
        locations.append(
            {
                "player_name": player.player_name,
                "location": player.position,
            }
        )
    return locations


# --------------- Deck Functions -----------------


@db_session
def _get_discard_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=True)


@db_session
def _get_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=False)


@db_session
def new_deck_from_discard(match_id: int):
    """Pre: The match is initialized"""
    discard_deck = _get_discard_deck(match_id)
    deck = _get_deck(match_id)
    deck.cards = discard_deck.cards.copy()
    discard_deck.cards.clear()


@db_session
def pick_random_card(player_id: int) -> Card:
    """If the deck is empty, form a new deck from the discard deck"""
    player = get_player_by_id(player_id)
    match_id = player.match.id
    deck = _get_deck(match_id)
    if is_deck_empty(match_id):
        new_deck_from_discard(match_id)

    card = list(deck.cards.random(1))[0]
    player.cards.add(card)
    card.player.add(player)
    deck.cards.remove(card)
    card.deck.remove(deck)
    return card


@db_session
def db_get_player_match_id(player_name: str):
    if not player_exists(player_name):
        raise PlayerNotFound("Player not found")

    match = Player.get(player_name=player_name).match

    if match is None:
        raise PlayerNotInMatch("Player not in match")

    return match.id
