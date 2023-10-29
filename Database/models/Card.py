from pony.orm import *
from Database.Database import Card
from Database.exceptions import *
from Game.cards.cards import *


# --------- Card functions --------- #

TARGET_CARDS = [
    "Lanzallamas",
    "Análisis",
    "Sospecha",
    "Seducción",
    "¡Cambio de Lugar!",
    "¿No podemos ser amigos?",
    "Cuarentena",
    "Puerta atrancada",
    "Hacha",
    "¡Más vale que corras!",
    "Que quede entre nosotros...",
    "¡Sal de aquí!",
]
TARGET_ADJACENT = [
    "Lanzallamas",
    "Análisis",
    "Sospecha",
    "Hacha",
    "¡Cambio de Lugar!",
    "Cuarentena",
    "Puerta atrancada",
    "Que quede entre nosotros...",

]
TARGET_NOT_QUARANTINED = [
    "Seducción",
    "¡Más vale que corras!",
    "¡Cambio de Lugar!",
    "¿No podemos ser amigos?",
]
DEFENSIBLE_CARD = [
    "Lanzallamas",
    "¡Cambio de Lugar!",
    "¡Más vale que corras!",
]
DEFEND_EXCHANGE = [
    "Aterrador",
    "¡No, gracias!",
    "¡Fallaste!",
]
GLOBAL_EXCHANGE = [
    "Seducción",
    "¿No podemos ser amigos?"
]

@db_session
def get_card_by_id(card_id: int) -> Card:
    if not Card.exists(id=card_id):
        raise CardNotFound("Carta no encontrada")
    return Card[card_id]


@db_session
def card_exists(card_id: int) -> bool:
    return Card.exists(id=card_id)


@db_session
def get_card_name(card_id: int) -> str:
    return get_card_by_id(card_id).card_name


@db_session
def is_defensa(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.DEFENSA.value


@db_session
def is_panic(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.PANICO.value


@db_session
def is_contagio(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.CONTAGIO.value


@db_session
def has_defense(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in DEFENSIBLE_CARD


@db_session
def defend_exchange(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in DEFEND_EXCHANGE


@db_session
def get_card_type(card_id: int) -> int:
    return get_card_by_id(card_id).type


@db_session
def requires_target(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in TARGET_CARDS


@db_session
def requires_adjacent_target(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in TARGET_ADJACENT


@db_session
def requires_target_not_quarantined(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in TARGET_NOT_QUARANTINED

@db_session
def allows_global_exchange(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in GLOBAL_EXCHANGE


# ----- Register Cards ----- #


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
