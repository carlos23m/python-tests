# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
import pytest
import httpx

BOOKER_BASE = "https://restful-booker.herokuapp.com"


@pytest.fixture(scope="session")
def booker_url():
    return BOOKER_BASE


@pytest.fixture(scope="session")
def auth_token(booker_url):
    """Obtain a real token from Restful-booker once per session."""
    # session-scoped: token doesn't expire mid-suite, so one request is enough
    resp = httpx.post(
        f"{booker_url}/auth",
        json={"username": "admin", "password": "password123"},
        timeout=10,
    )
    assert resp.status_code == 200, f"Auth failed: {resp.text}"
    token = resp.json().get("token")
    assert token, "No token in auth response"
    return token


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    # Restful-booker uses Cookie-based auth, not a Bearer token in Authorization header
    return {"Cookie": f"token={auth_token}"}
