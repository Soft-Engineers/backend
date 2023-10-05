from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *

def print_cards(player):
    for c in player.cards:
            print(c.number)
            print(c.card_name)
            print(c.id)
            print("---------------")

"""
Completar tests luego de codear iniciar partida
"""

class test_iniciar_partida(TestCase):
    def test_iniciar_partida(self):
        """
        create_player("player1")
        create_player("player2")
        create_player("player3")
        create_player("player4")
        db_create_match("match1","player1",4,4)
        db_add_player("player2","match1")
        db_add_player("player3","match1")
        db_add_player("player4","match1")
        """
        pass