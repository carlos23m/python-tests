# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Auth / token endpoint — restful-booker.herokuapp.com/auth
"""
import httpx


def test_valid_credentials_return_token(booker_url):
    """Happy path: correct credentials return a non-empty token string."""
    resp = httpx.post(
        f"{booker_url}/auth",
        json={"username": "admin", "password": "password123"},
        timeout=10,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "token" in body
    assert isinstance(body["token"], str)
    assert len(body["token"]) > 0


def test_wrong_password_returns_bad_credentials(booker_url):
    """Wrong password returns 200 with a reason field instead of a token — API quirk."""
    resp = httpx.post(
        f"{booker_url}/auth",
        json={"username": "admin", "password": "wrong"},
        timeout=10,
    )
    # Restful-booker returns 200 with {"reason": "Bad credentials"} for wrong creds
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("reason") == "Bad credentials"


def test_missing_password_field(booker_url):
    """Omitting the password key should signal an error, not silently succeed."""
    # TODO: send {"username": "admin"} with no password key
    # assert the response signals an error (reason field or non-200 status)
    ...


def test_empty_body_does_not_crash_server(booker_url):
    """An empty JSON body should not cause a 500 — the server must handle it gracefully."""
    # TODO: POST {} to /auth
    # assert status is not 500
    ...
