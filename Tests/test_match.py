from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient


client = TestClient(app)


def test_match_listing():
    with patch("app.get_match_list", return_value=[1, 2, 3]):
        response = client.get("/match/list")
        assert response.status_code == 200
        assert response.json() == {"Matches": [1, 2, 3]}
