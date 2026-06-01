# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Full CRUD cycle against restful-booker.herokuapp.com/booking
"""
import httpx
import pytest

BOOKING_PAYLOAD = {
    "firstname": "Carlos",
    "lastname": "QA",
    "totalprice": 150,
    "depositpaid": True,
    "bookingdates": {"checkin": "2026-07-01", "checkout": "2026-07-05"},
    "additionalneeds": "Breakfast",
}


# ── CREATE ────────────────────────────────────────────────────────────────────

def test_create_booking_returns_201_and_id(booker_url):
    """POST /booking returns 200 with an integer bookingid in the response body."""
    resp = httpx.post(f"{booker_url}/booking", json=BOOKING_PAYLOAD, timeout=10)
    assert resp.status_code == 200  # Restful-booker uses 200 on create (not 201)
    body = resp.json()
    assert "bookingid" in body
    assert isinstance(body["bookingid"], int)


def test_create_booking_response_shape(booker_url):
    """The booking object echoed in the create response matches the submitted payload."""
    resp = httpx.post(f"{booker_url}/booking", json=BOOKING_PAYLOAD, timeout=10)
    booking = resp.json()["booking"]
    assert booking["firstname"] == BOOKING_PAYLOAD["firstname"]
    assert booking["totalprice"] == BOOKING_PAYLOAD["totalprice"]
    assert booking["bookingdates"]["checkin"] == BOOKING_PAYLOAD["bookingdates"]["checkin"]


# ── READ ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def created_booking_id(booker_url):
    """Create one booking and return its ID for use in read/update/delete tests."""
    # module-scoped: shared across all CRUD tests so only one booking is created on the server
    resp = httpx.post(f"{booker_url}/booking", json=BOOKING_PAYLOAD, timeout=10)
    return resp.json()["bookingid"]


def test_get_booking_by_id_returns_200(booker_url, created_booking_id):
    """GET /booking/{id} returns 200 for a booking that exists."""
    resp = httpx.get(f"{booker_url}/booking/{created_booking_id}", timeout=10)
    assert resp.status_code == 200


def test_get_booking_fields_match_created_payload(booker_url, created_booking_id):
    """Fields returned by GET match the values that were submitted on creation."""
    resp = httpx.get(f"{booker_url}/booking/{created_booking_id}", timeout=10)
    body = resp.json()
    assert body["firstname"] == BOOKING_PAYLOAD["firstname"]
    assert body["lastname"] == BOOKING_PAYLOAD["lastname"]
    assert body["totalprice"] == BOOKING_PAYLOAD["totalprice"]


def test_list_bookings_returns_array(booker_url):
    """GET /booking returns a list of objects each containing a bookingid."""
    resp = httpx.get(f"{booker_url}/booking", timeout=10)
    assert resp.status_code == 200
    ids = resp.json()
    assert isinstance(ids, list)
    assert all("bookingid" in item for item in ids)


# ── UPDATE (PUT) ──────────────────────────────────────────────────────────────

def test_full_update_requires_auth(booker_url, created_booking_id):
    """PUT without a token is rejected with 403."""
    updated = {**BOOKING_PAYLOAD, "totalprice": 999}
    resp = httpx.put(
        f"{booker_url}/booking/{created_booking_id}",
        json=updated,
        timeout=10,
    )
    # without token Restful-booker returns 403
    assert resp.status_code == 403


def test_full_update_with_auth_returns_200(booker_url, created_booking_id, auth_headers):
    """Authenticated PUT replaces the booking and returns the updated resource."""
    updated = {**BOOKING_PAYLOAD, "totalprice": 999}
    resp = httpx.put(
        f"{booker_url}/booking/{created_booking_id}",
        json=updated,
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["totalprice"] == 999


# ── PARTIAL UPDATE (PATCH) ────────────────────────────────────────────────────

def test_partial_update_firstname(booker_url, created_booking_id, auth_headers):
    """PATCH updates only the submitted field; all other fields are unchanged."""
    before = httpx.get(f"{booker_url}/booking/{created_booking_id}", timeout=10).json()

    resp = httpx.patch(
        f"{booker_url}/booking/{created_booking_id}",
        json={"firstname": "Updated"},
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code == 200
    after = resp.json()
    assert after["firstname"] == "Updated"
    assert after["lastname"] == before["lastname"]
    assert after["totalprice"] == before["totalprice"]
    assert after["bookingdates"] == before["bookingdates"]


# ── DELETE ────────────────────────────────────────────────────────────────────

def test_delete_requires_auth(booker_url, created_booking_id):
    """DELETE without a token is rejected with 403."""
    resp = httpx.delete(f"{booker_url}/booking/{created_booking_id}", timeout=10)
    assert resp.status_code == 403


def test_delete_with_auth_returns_201(booker_url, auth_headers):
    """Authenticated DELETE removes the booking; a subsequent GET returns 404."""
    # Create a throwaway booking so deleting it doesn't affect the shared created_booking_id fixture
    resp = httpx.post(f"{booker_url}/booking", json={
        "firstname": "Delete", "lastname": "Me", "totalprice": 1,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-09-01", "checkout": "2026-09-02"},
    }, timeout=10)
    assert resp.status_code == 200
    booking_id = resp.json()["bookingid"]

    resp = httpx.delete(
        f"{booker_url}/booking/{booking_id}", headers=auth_headers, timeout=10
    )
    # Restful-booker returns 201 (not 204) on successful delete — quirk of the API
    assert resp.status_code == 201

    # Confirm the booking is truly gone
    resp = httpx.get(f"{booker_url}/booking/{booking_id}", timeout=10)
    assert resp.status_code == 404
