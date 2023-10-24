from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from Game.app_auxiliars import *

class test_generate_unique_testing_name(TestCase):
    def test_generate_unique_testing_name(self):
        prefix = "TName"
        a = generate_unique_testing_name()
        b = generate_unique_testing_name()
        a_id = int(a[len(prefix) :])
        b_id = int(b[len(prefix) :])

        self.assertTrue(a.startswith(prefix))
        self.assertTrue(b.startswith(prefix))
        self.assertTrue(a_id == b_id - 1)


class test_get_random_string_lower(TestCase):
    def test_get_random_string_lower(self):
        length = 50
        a = get_random_string_lower(length)
        b = get_random_string_lower(length)

        self.assertTrue(a.islower())
        self.assertTrue(b.islower())
        self.assertTrue(len(a) == length)
        self.assertTrue(len(b) == length)
        self.assertTrue(a != b)


class test_get_random_string_upper(TestCase):
    def test_get_random_string_upper(self):
        length = 50
        a = get_random_string_upper(length)
        b = get_random_string_upper(length)

        self.assertTrue(a.isupper())
        self.assertTrue(b.isupper())
        self.assertTrue(len(a) == length)
        self.assertTrue(len(b) == length)
        self.assertTrue(a != b)


class test_get_random_string_num(TestCase):
    def test_get_random_string_num(self):
        length = 50
        a = get_random_string_num(length)
        b = get_random_string_num(length)

        self.assertTrue(a.isnumeric())
        self.assertTrue(b.isnumeric())
        self.assertTrue(len(a) == length)
        self.assertTrue(len(b) == length)
        self.assertTrue(a != b)
