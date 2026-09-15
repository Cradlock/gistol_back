import unittest

from app.main import app
from app.schemas.students import StudentUpdate
from app.models.years import Year


class StudentEditContractTests(unittest.TestCase):
    def test_patch_student_reads_json_body_not_query(self):
        spec = app.openapi()["paths"]["/api/student/{user_id}"]["patch"]
        self.assertIn("requestBody", spec)
        query_names = {
            param["name"]
            for param in spec.get("parameters", [])
            if param.get("in") == "query"
        }
        self.assertFalse(
            {"surname", "name", "group_id", "year", "scores"} & query_names
        )

    def test_dashboard_payload_matches_schema(self):
        data = StudentUpdate.model_validate(
            {
                "surname": "Ivanov",
                "name": "Ivan",
                "group_id": 4,
                "year": 2,
                "scores": 12,
            }
        )
        self.assertEqual(data.year, Year.SECOND)
        self.assertEqual(data.group_id, 4)


if __name__ == "__main__":
    unittest.main()
