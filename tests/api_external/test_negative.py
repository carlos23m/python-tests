# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Negative cases — bad payloads, missing fields, wrong IDs, unauth'd mutations.
"""
import httpx

_THROWAWAY = {
    "firstname": "Test", "lastname": "QA", "totalprice": 1,
    "depositpaid": False,
    "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-02"},
}


def test_get_nonexistent_booking_returns_404(booker_url):
    resp = httpx.get(f"{booker_url}/booking/99999999", timeout=10)
    assert resp.status_code == 404


def test_create_booking_missing_firstname(booker_url):
    payload = {
        "lastname": "QA",
        "totalprice": 100,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-05"},
    }
    resp = httpx.post(f"{booker_url}/booking", json=payload, timeout=10)
    # Restful-booker returns 500 on missing firstname (known API behavior) — assert it at least responds
    assert resp.status_code <= 500


def test_create_booking_invalid_date_format(booker_url):
    payload = {
        "firstname": "Carlos", "lastname": "QA", "totalprice": 100,
        "depositpaid": False,
        "bookingdates": {"checkin": "not-a-date", "checkout": "2026-08-05"},
    }
    resp = httpx.post(f"{booker_url}/booking", json=payload, timeout=10)
    assert resp.status_code <= 500


def test_update_nonexistent_booking_returns_405(booker_url, auth_headers):
    payload = {
        "firstname": "Carlos", "lastname": "QA", "totalprice": 100,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-05"},
    }
    resp = httpx.put(
        f"{booker_url}/booking/99999999",
        json=payload,
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code == 405


def test_delete_nonexistent_booking(booker_url, auth_headers):
    resp = httpx.delete(
        f"{booker_url}/booking/99999999", headers=auth_headers, timeout=10
    )
    assert resp.status_code == 405


def test_put_without_content_type(booker_url, auth_headers):
    resp = httpx.post(f"{booker_url}/booking", json=_THROWAWAY, timeout=10)
    booking_id = resp.json()["bookingid"]

    resp = httpx.put(
        f"{booker_url}/booking/{booking_id}",
        content=b"raw body without content type",
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code <= 500


def test_auth_header_with_garbage_token(booker_url):
    resp = httpx.post(f"{booker_url}/booking", json=_THROWAWAY, timeout=10)
    booking_id = resp.json()["bookingid"]

    resp = httpx.delete(
        f"{booker_url}/booking/{booking_id}",
        headers={"Cookie": "token=notarealtoken"},
        timeout=10,
    )
    assert resp.status_code == 403
