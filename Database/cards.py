from enum import Enum

# amount indica la cantidad de veces que se encuentra una carta con
# card_name y number repetido.


class CardType(Enum):
    CONTAGIO = 1
    DEFENSA = 2
    ACCION = 3
    OBSTACULO = 4
    PANICO = 5


class T:
    def __init__(self, number: int, amount: int):
        if number is not None and (number < 3 or number > 12):
            raise Exception("Inconsistent card number")
        if amount is None or amount < 1:
            raise Exception("Inconsistent card amount")

        self.number = number
        self.amount = amount

    def __eq__(self, __value: object) -> bool:
        return self.number == __value.number and self.amount == __value.amount


class CardTemplate:
    def __init__(self, card_name: str, repetitions: list[T], type: CardType):
        self.card_name = card_name
        self.repetitions = repetitions
        self.type = type


card_templates = [
    CardTemplate("La Cosa", [T(None, 1)], CardType.CONTAGIO),
    CardTemplate(
        "¡Infectado!",
        [T(4, 8), T(6, 2), T(7, 2), T(8, 1), T(9, 2), T(10, 2), T(11, 3)],
        CardType.CONTAGIO,
    ),
    CardTemplate("Lanzallamas", [T(4, 2), T(6, 1), T(9, 1), T(11, 1)], CardType.ACCION),
    CardTemplate("Análisis", [T(5, 1), T(6, 1), T(9, 1)], CardType.ACCION),
    CardTemplate("Hacha", [T(4, 1), T(9, 1)], CardType.ACCION),
    CardTemplate(
        "Sospecha", [T(4, 4), T(7, 1), T(8, 1), T(9, 1), T(10, 1)], CardType.ACCION
    ),
    CardTemplate(
        "Determinación", [T(4, 2), T(6, 1), T(9, 1), T(10, 1)], CardType.ACCION
    ),
    CardTemplate("Whisky", [T(4, 1), T(6, 1), T(10, 1)], CardType.ACCION),
    CardTemplate(
        "¡Cambio de Lugar!", [T(4, 2), T(7, 1), T(9, 1), T(11, 1)], CardType.ACCION
    ),
    CardTemplate("Vigila tus espaldas", [T(4, 1), T(9, 1)], CardType.ACCION),
    CardTemplate(
        "Seducción",
        [T(4, 2), T(6, 1), T(7, 1), T(8, 1), T(10, 1), T(11, 1)],
        CardType.ACCION,
    ),
    CardTemplate("Puerta atrancada", [T(4, 1), T(7, 1), T(11, 1)], CardType.OBSTACULO),
    CardTemplate(
        "¡Más vale que corras!", [T(4, 2), T(7, 1), T(9, 1), T(11, 1)], CardType.ACCION
    ),
    CardTemplate("Aquí estoy bien", [T(4, 1), T(6, 1), T(11, 1)], CardType.DEFENSA),
    CardTemplate("Aterrador", [T(5, 1), T(6, 1), T(8, 1), T(11, 1)], CardType.ACCION),
    CardTemplate(
        "¡No, gracias!", [T(4, 1), T(6, 1), T(8, 1), T(11, 1)], CardType.DEFENSA
    ),
    CardTemplate("¡Fallaste!", [T(4, 1), T(6, 1), T(11, 1)], CardType.DEFENSA),
    CardTemplate("¡Nada de barbacoas!", [T(4, 1), T(6, 1), T(11, 1)], CardType.DEFENSA),
    CardTemplate("Cuartentena", [T(5, 1), T(9, 1)], CardType.OBSTACULO),
    CardTemplate("Revelaciones", [T(8, 1)], CardType.PANICO),
    CardTemplate("Cuerdas podridas", [T(6, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("¡Sal de aquí!", [T(5, 1)], CardType.PANICO),
    CardTemplate("Olvidadizo", [T(4, 1)], CardType.PANICO),
    CardTemplate("Uno, dos..", [T(5, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("Tres, cuatro..", [T(4, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("¿Es aquí la fiesta?", [T(5, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("Que quede entre nosotros...", [T(7, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("Vuelta y vuelta", [T(4, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("¿No podemos ser amigos?", [T(7, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("Cita a ciegas", [T(4, 1), T(9, 1)], CardType.PANICO),
    CardTemplate("¡Ups!", [T(10, 1)], CardType.PANICO),
    # Hay 108 cartas, falta una. Cuál?
]


def pretty_print_cards():
    print("----------------------------------")
    for card in card_templates:
        for tuple in card.repetitions:
            for _ in range(tuple.amount):
                print("card_name: " + card.card_name)
                print("card_number: " + str(tuple.number))
                print("card_number: " + card.type.name)
                print("----------------------------------")


def amount_cards():
    amount = 0
    for card in card_templates:
        for tuple in card.repetitions:
            amount += tuple.amount
    return amount
