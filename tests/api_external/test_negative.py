# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Negative cases — bad payloads, missing fields, wrong IDs, unauth'd mutations.
"""
import httpx
import pytest


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
    # Restful-booker is lenient — assert it does NOT return a 5xx
    assert resp.status_code < 500


def test_create_booking_invalid_date_format(booker_url):
    # TODO: send bookingdates with "checkin": "not-a-date"
    # assert status < 500 (server must not crash)
    ...


def test_update_nonexistent_booking_returns_405(booker_url, auth_headers):
    # TODO: PUT /booking/99999999 with a valid payload + auth
    # assert 405 (Restful-booker's response for missing resource on update)
    ...


def test_delete_nonexistent_booking(booker_url, auth_headers):
    # TODO: DELETE /booking/99999999 with auth
    # assert 405
    ...


def test_put_without_content_type(booker_url, auth_headers):
    # TODO: send a PUT with raw bytes body and no Content-Type header
    # assert status < 500
    ...


def test_auth_header_with_garbage_token(booker_url):
    # TODO: attempt a DELETE with Cookie: token=notarealtoken
    # assert 403
    ...
