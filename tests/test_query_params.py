import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.query import OptionalIntQuery


app = FastAPI()


@app.get("/items")
def list_items(group_id: OptionalIntQuery = None):
    return {"group_id": group_id}


class OptionalIntQueryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_empty_group_id_is_none(self):
        response = self.client.get("/items", params={"group_id": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"group_id": None})

    def test_missing_group_id_is_none(self):
        response = self.client.get("/items")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"group_id": None})

    def test_numeric_group_id_is_parsed(self):
        response = self.client.get("/items", params={"group_id": "12"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"group_id": 12})


if __name__ == "__main__":
    unittest.main()
