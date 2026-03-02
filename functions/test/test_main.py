from unittest.mock import MagicMock, patch

from firebase_admin.auth import InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError, UserDisabledError

from functions.main import on_request, is_authenticated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(method="GET", headers=None):
    if headers is None:
        headers = make_auth_headers()
    req = MagicMock()
    req.method = method
    req.headers = headers or {}
    return req


def make_auth_headers(token="valid-token"):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# is_authenticated
# ---------------------------------------------------------------------------

class TestIsAuthenticated:
    def test_valid_token(self):
        with patch("main.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = {"uid": "user1"}
            req = make_request(headers=make_auth_headers("good-token"))
            assert is_authenticated(req) is True
            mock_verify.assert_called_once_with("good-token")

    def test_missing_authorization_header(self):
        req = make_request(headers={})
        assert is_authenticated(req) is False

    def test_authorization_not_bearer(self):
        req = make_request(headers={"Authorization": "Basic some-token"})
        assert is_authenticated(req) is False

    def test_invalid_token(self):
        with patch("main.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = InvalidIdTokenError("invalid")
            req = make_request(headers=make_auth_headers("bad-token"))
            assert is_authenticated(req) is False

    def test_expired_token(self):
        with patch("main.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = ExpiredIdTokenError("expired", cause=None)
            req = make_request(headers=make_auth_headers("expired-token"))
            assert is_authenticated(req) is False

    def test_revoked_token(self):
        with patch("main.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = RevokedIdTokenError("revoked")
            req = make_request(headers=make_auth_headers("revoked-token"))
            assert is_authenticated(req) is False

    def test_user_disabled(self):
        with patch("main.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = UserDisabledError("disabled")
            req = make_request(headers=make_auth_headers("disabled-token"))
            assert is_authenticated(req) is False

# ---------------------------------------------------------------------------
# on_request
# ---------------------------------------------------------------------------

class TestOnRequest:
    def test_unauthenticated_request_returns_401(self):
        req = make_request(headers={})
        with patch("main.is_authenticated", return_value=False):
            response = on_request(req)
        assert response.status_code == 401

    def test_get_routes_to_get_handler(self):
        req = make_request(method="GET")
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}), \
             patch("https_method_handlers.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            on_request(req)
            mock_get.assert_called_once()

    def test_post_routes_to_post_handler(self):
        req = make_request(method="POST")
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}), \
             patch("https_method_handlers.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201)
            on_request(req)
            mock_post.assert_called_once()

    def test_put_routes_to_put_handler(self):
        req = make_request(method="PUT")
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}), \
             patch("https_method_handlers.put") as mock_put:
            mock_put.return_value = MagicMock(status_code=200)
            on_request(req)
            mock_put.assert_called_once()

    def test_delete_routes_to_delete_handler(self):
        req = make_request(method="DELETE")
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}), \
             patch("https_method_handlers.delete") as mock_delete:
            mock_delete.return_value = MagicMock(status_code=200)
            on_request(req)
            mock_delete.assert_called_once()

    def test_unsupported_method_returns_405(self):
        req = make_request(method="PATCH")
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}):
            response = on_request(req)
        assert response.status_code == 405

    def test_handler_response_is_returned(self):
        req = make_request(method="GET")
        expected_response = MagicMock(status_code=200)
        with patch("main.auth.verify_id_token", return_value={"uid": "user1"}), \
             patch("https_method_handlers.get", return_value=expected_response):
            response = on_request(req)
        assert response == expected_response