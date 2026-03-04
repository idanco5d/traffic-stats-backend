import json
from unittest.mock import MagicMock

from functions.https_method_handlers import get, post, put, delete, is_valid_traffic_stat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(method="GET", args=None, json_body=None):
    req = MagicMock()
    req.method = method
    req.args = args or {}
    req.get_json.return_value = json_body
    return req


def make_doc(doc_id: str, data: dict):
    doc = MagicMock()
    doc.id = doc_id
    doc.to_dict.return_value = data
    return doc


def make_doc_ref(doc_id: str, data: dict, exists: bool = True):
    doc_snapshot = MagicMock()
    doc_snapshot.exists = exists
    doc_snapshot.id = doc_id

    doc_ref = MagicMock()
    doc_ref.id = doc_id
    doc_ref.get.return_value = doc_snapshot
    return doc_ref


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

class TestGet:
    def test_fetch_first_page(self):
        doc = make_doc("abc123", {"date": "2024-01-01", "visits": 5})
        db = MagicMock()
        db.collection.return_value.offset.return_value.limit.return_value.stream.return_value = [doc]
        db.collection.return_value.count.return_value.get.return_value = [[MagicMock(value=1)]]

        req = make_request(args={"offset": "0"})
        response = get(req, db)

        assert response.status_code == 200
        body = json.loads(response.get_data())
        assert body["totalEntries"] == 1
        assert body["page"] == 1
        assert body["totalPages"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0] == {"id": "abc123", "date": "2024-01-01", "visits": 5}
        db.collection.return_value.offset.assert_called_once_with(0)

    def test_fetch_second_page(self):
        doc = make_doc("def456", {"date": "2024-01-11", "visits": 3})
        db = MagicMock()
        db.collection.return_value.offset.return_value.limit.return_value.stream.return_value = [doc]
        db.collection.return_value.count.return_value.get.return_value = [[MagicMock(value=11)]]

        req = make_request(args={"offset": "10"})
        response = get(req, db)

        assert response.status_code == 200
        body = json.loads(response.get_data())
        assert body["totalEntries"] == 11
        assert body["page"] == 2
        assert body["totalPages"] == 2
        assert len(body["data"]) == 1
        assert body["data"][0]["id"] == "def456"
        db.collection.return_value.offset.assert_called_once_with(10)


# ---------------------------------------------------------------------------
# POST
# ---------------------------------------------------------------------------

class TestPost:
    def test_successful_insertion(self):
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        new_doc_ref = MagicMock()
        new_doc_ref.id = "newid123"
        db.collection.return_value.add.return_value = (None, new_doc_ref)

        req = make_request(method="POST", json_body={"date": "2024-03-01", "visits": 10})
        response = post(req, db)

        assert response.status_code == 201
        body = json.loads(response.get_data())
        assert body["id"] == "newid123"

    def test_invalid_stat_visits_is_string(self):
        db = MagicMock()
        req = make_request(method="POST", json_body={"date": "2024-03-01", "visits": "ten"})
        response = post(req, db)

        assert response.status_code == 422
        db.collection.return_value.add.assert_not_called()

    def test_date_already_exists(self):
        existing_doc = make_doc("existing1", {"date": "2024-03-01", "visits": 5})
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = [existing_doc]

        req = make_request(method="POST", json_body={"date": "2024-03-01", "visits": 10})
        response = post(req, db)

        assert response.status_code == 409
        db.collection.return_value.add.assert_not_called()


# ---------------------------------------------------------------------------
# PUT
# ---------------------------------------------------------------------------

class TestPut:
    def test_successful_update(self):
        doc_id = "doc1"
        db = MagicMock()

        # Existing document
        doc_ref = make_doc_ref(doc_id, {"date": "2024-03-01", "visits": 1})
        db.collection.return_value.document.return_value = doc_ref

        # No conflicting date
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []

        req = make_request(method="PUT", args={"id": doc_id}, json_body={"date": "2024-03-01", "visits": 2})
        response = put(req, db)

        assert response.status_code == 200
        doc_ref.set.assert_called_once_with({"date": "2024-03-01", "visits": 2})

    def test_missing_doc_id(self):
        db = MagicMock()
        req = make_request(method="PUT", args={}, json_body={"date": "2024-03-01", "visits": 2})
        response = put(req, db)

        assert response.status_code == 400
        db.collection.return_value.document.assert_not_called()

    def test_invalid_stat_visits_is_string(self):
        db = MagicMock()
        req = make_request(method="PUT", args={"id": "doc1"}, json_body={"date": "2024-03-01", "visits": "two"})
        response = put(req, db)

        assert response.status_code == 422
        db.collection.return_value.document.assert_not_called()

    def test_doc_id_not_found(self):
        db = MagicMock()
        doc_ref = make_doc_ref("ghost", {}, exists=False)
        db.collection.return_value.document.return_value = doc_ref

        req = make_request(method="PUT", args={"id": "ghost"}, json_body={"date": "2024-03-01", "visits": 2})
        response = put(req, db)

        assert response.status_code == 404
        doc_ref.set.assert_not_called()

    def test_date_belongs_to_another_document(self):
        doc_id = "doc1"
        other_doc_id = "doc2"

        db = MagicMock()
        doc_ref = make_doc_ref(doc_id, {"date": "2024-03-01", "visits": 1})
        db.collection.return_value.document.return_value = doc_ref

        # Conflicting date belongs to a different document
        conflicting_doc = make_doc(other_doc_id, {"date": "2024-03-02", "visits": 7})
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = [conflicting_doc]

        req = make_request(method="PUT", args={"id": doc_id}, json_body={"date": "2024-03-02", "visits": 2})
        response = put(req, db)

        assert response.status_code == 409
        doc_ref.set.assert_not_called()


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

class TestDelete:
    def test_successful_deletion(self):
        doc_id = "doc1"
        db = MagicMock()
        doc_ref = make_doc_ref(doc_id, {"date": "2024-03-01", "visits": 5})
        db.collection.return_value.document.return_value = doc_ref

        req = make_request(method="DELETE", args={"id": doc_id})
        response = delete(req, db)

        assert response.status_code == 200
        doc_ref.delete.assert_called_once()

    def test_missing_doc_id(self):
        db = MagicMock()
        req = make_request(method="DELETE", args={})
        response = delete(req, db)

        assert response.status_code == 400
        db.collection.return_value.document.assert_not_called()

    def test_doc_id_not_found(self):
        db = MagicMock()
        doc_ref = make_doc_ref("ghost", {}, exists=False)
        db.collection.return_value.document.return_value = doc_ref

        req = make_request(method="DELETE", args={"id": "ghost"})
        response = delete(req, db)

        assert response.status_code == 404
        doc_ref.delete.assert_not_called()


# ---------------------------------------------------------------------------
# is_valid_traffic_stat
# ---------------------------------------------------------------------------

class TestIsValidTrafficStat:
    def test_date_not_a_string(self):
        assert is_valid_traffic_stat({"date": 20240101, "visits": 5}) is False

    def test_date_not_included(self):
        assert is_valid_traffic_stat({"visits": 5}) is False

    def test_visits_not_included(self):
        assert is_valid_traffic_stat({"date": "2024-01-01"}) is False

    def test_date_wrong_format(self):
        assert is_valid_traffic_stat({"date": "01-01-2024", "visits": 5}) is False

    def test_visits_negative(self):
        assert is_valid_traffic_stat({"date": "2024-01-01", "visits": -1}) is False