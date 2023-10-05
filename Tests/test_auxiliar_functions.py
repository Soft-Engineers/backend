from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *


class test_db_add_player(TestCase):
    def test_generate_unique_testing_name(self):
        prefix = "TName"
        a = generate_unique_testing_name()
        b = generate_unique_testing_name()
        a_id = int(a[len(prefix) :])
        b_id = int(b[len(prefix) :])

        self.assertTrue(a.startswith(prefix))
        self.assertTrue(b.startswith(prefix))
        self.assertTrue(a_id == b_id - 1)
