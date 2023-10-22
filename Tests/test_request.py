from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from request import parse_request, RequestException


class test_parse_request(TestCase):
    def test_parse_request(self):
        json = '{"message_type": "test", "message_content": "test_content"}'

        type, content = parse_request(json)

        self.assertEqual(type, "test")
        self.assertEqual(content, "test_content")

    def test_parse_request_invalid(self):
        json = '{"message_type": "test", "message_content": "test_content"'

        with self.assertRaises(RequestException):
            parse_request(json)
