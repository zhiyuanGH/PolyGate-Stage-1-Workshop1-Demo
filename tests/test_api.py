"""Business-level checks for the four Workshop 1 mock APIs.

Every test uses a temporary SQLite database. The checked-in sample data and
any database used during a workshop are never changed by this test suite.
"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Barrier

from fastapi.testclient import TestClient
import pytest

from booking_demo.app import create_app


SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_data.json"
EXAMPLE = {
    "user_id": "U1",
    "court_id": "B01",
    "date": "2026-11-05",
    "start_time": "18:00",
    "end_time": "19:00",
}


def booking(**changes):
    return {**EXAMPLE, **changes}


def window(**changes):
    return {key: value for key, value in booking(**changes).items() if key != "user_id"}


def user_bookings(client, user_id="U1"):
    response = client.get("/bookings", params={"user_id": user_id})
    assert response.status_code == 200, response.text
    return response.json()["bookings"]


@pytest.fixture
def client(tmp_path):
    application = create_app(db_path=tmp_path / "test.sqlite3", seed_path=SEED_PATH)
    with TestClient(application) as test_client:
        yield test_client


def test_court_details_match_the_seed(client):
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    expected = next(court for court in seed["courts"] if court["court_id"] == "B01")

    response = client.get("/courts/B01")

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    ("start_time", "end_time", "available"),
    [("16:00", "17:00", False), ("18:00", "19:00", True)],
    ids=["seeded-booking", "available-time"],
)
def test_availability_reports_the_requested_window(client, start_time, end_time, available):
    query = window(start_time=start_time, end_time=end_time)

    response = client.get("/availability", params=query)

    assert response.status_code == 200
    assert response.json() == {**query, "available": available}
    assert user_bookings(client) == []  # Checking a time does not reserve it.


def test_booking_workflow_saves_and_returns_the_same_details(client):
    assert user_bookings(client) == []

    created = client.post("/bookings", json=booking())

    assert created.status_code == 201, created.text
    assert created.json() == {"booking_id": "BK-001", "status": "confirmed"}
    assert user_bookings(client) == [{"booking_id": "BK-001", **booking()}]
    assert client.get("/availability", params=window()).json()["available"] is False

    # A rejected repeat must neither add a record nor alter the saved booking.
    rejected = client.post("/bookings", json=booking())
    assert rejected.status_code == 409
    assert user_bookings(client) == [{"booking_id": "BK-001", **booking()}]


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [("15:30", "16:30"), ("16:30", "17:30"), ("15:30", "17:30"), ("16:15", "16:45")],
    ids=["overlap-start", "overlap-end", "encloses-booking", "inside-booking"],
)
def test_all_overlap_shapes_reject_without_saving(client, start_time, end_time):
    original = user_bookings(client, "U2")
    query = window(start_time=start_time, end_time=end_time)

    assert client.get("/availability", params=query).json()["available"] is False
    response = client.post("/bookings", json=booking(start_time=start_time, end_time=end_time))

    assert response.status_code == 409
    assert user_bookings(client) == []
    assert user_bookings(client, "U2") == original
    # A rejected insert does not consume the first generated booking number.
    assert client.post("/bookings", json=booking()).json()["booking_id"] == "BK-001"


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [("15:00", "16:00"), ("17:00", "18:00")],
    ids=["ends-at-existing-start", "starts-at-existing-end"],
)
def test_adjacent_bookings_are_allowed(client, start_time, end_time):
    payload = booking(start_time=start_time, end_time=end_time)

    assert client.get("/availability", params=window(start_time=start_time, end_time=end_time)).json()["available"] is True
    response = client.post("/bookings", json=payload)

    assert response.status_code == 201
    assert user_bookings(client) == [{"booking_id": "BK-001", **payload}]


@pytest.mark.parametrize(
    "changes",
    [{"court_id": "B02"}, {"date": "2026-11-06"}],
    ids=["different-court", "different-date"],
)
def test_bookings_on_other_courts_or_dates_do_not_conflict(client, changes):
    payload = booking(start_time="16:00", end_time="17:00", **changes)
    query = {key: value for key, value in payload.items() if key != "user_id"}

    assert client.get("/availability", params=query).json()["available"] is True
    assert client.post("/bookings", json=payload).status_code == 201


def test_unknown_court_is_404_and_cannot_be_booked(client):
    assert client.get("/courts/B99").status_code == 404
    assert client.get("/availability", params=window(court_id="B99")).status_code == 404
    assert client.post("/bookings", json=booking(court_id="B99")).status_code == 404
    assert user_bookings(client) == []


@pytest.mark.parametrize("missing_field", list(EXAMPLE))
def test_every_booking_field_is_required(client, missing_field):
    payload = booking()
    del payload[missing_field]

    assert client.post("/bookings", json=payload).status_code == 422
    assert user_bookings(client) == []


def test_extra_booking_fields_are_rejected(client):
    response = client.post("/bookings", json=booking(booking_id="CALLER-CHOSEN"))

    assert response.status_code == 422
    assert user_bookings(client) == []


@pytest.mark.parametrize("bad_date", ["2026-11-31", "2026-1-05", "2026-11-05T00:00:00"])
def test_date_must_be_a_real_date_in_exact_format(client, bad_date):
    assert client.post("/bookings", json=booking(date=bad_date)).status_code == 422
    assert user_bookings(client) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start_time", "8:00"),
        ("start_time", "18:00:00"),
        ("start_time", "18:00+08:00"),
        ("end_time", "24:00"),
        ("end_time", "19:60"),
    ],
)
def test_times_must_be_valid_hh_mm_local_times(client, field, value):
    assert client.post("/bookings", json=booking(**{field: value})).status_code == 422
    assert user_bookings(client) == []


@pytest.mark.parametrize("end_time", ["18:00", "17:00"], ids=["zero-duration", "reverse-order"])
def test_end_time_must_be_after_start_time(client, end_time):
    assert client.post("/bookings", json=booking(end_time=end_time)).status_code == 422
    assert user_bookings(client) == []


@pytest.mark.parametrize(
    "query",
    [
        {key: value for key, value in window().items() if key != "date"},
        window(date="2026-02-30"),
        window(end_time="17:00"),
        {**window(), "unexpected": "value"},
    ],
    ids=["missing-date", "invalid-date", "reverse-times", "extra-query-field"],
)
def test_availability_validates_its_query_too(client, query):
    assert client.get("/availability", params=query).status_code == 422
    assert user_bookings(client) == []


def test_booking_queries_filter_users_and_return_empty_for_unused_user(client):
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    for user_id in ("U1", "U2", "U3", "UNUSED"):
        expected = [row for row in seed["bookings"] if row["user_id"] == user_id]
        assert user_bookings(client, user_id) == expected

    assert client.get("/bookings").status_code == 422
    assert client.get("/bookings", params={"user_id": "U1", "unexpected": "value"}).status_code == 422


@pytest.mark.parametrize(("field", "value"), [("user_id", 1), ("court_id", None)])
def test_non_string_identifiers_are_rejected(client, field, value):
    assert client.post("/bookings", json=booking(**{field: value})).status_code == 422
    assert user_bookings(client) == []


def test_teaching_dates_do_not_depend_on_todays_date(client):
    payload = booking(date="2020-01-01")

    response = client.post("/bookings", json=payload)

    assert response.status_code == 201
    assert user_bookings(client) == [{"booking_id": "BK-001", **payload}]


def test_bookings_persist_when_the_app_is_recreated(tmp_path):
    database = tmp_path / "persistent.sqlite3"
    with TestClient(create_app(db_path=database, seed_path=SEED_PATH)) as first:
        assert first.post("/bookings", json=booking()).status_code == 201

    with TestClient(create_app(db_path=database, seed_path=SEED_PATH)) as reopened:
        assert user_bookings(reopened) == [{"booking_id": "BK-001", **booking()}]
        assert [row["booking_id"] for row in user_bookings(reopened, "U2")] == ["BK-000"]
        assert reopened.get("/availability", params=window()).json()["available"] is False
        assert reopened.post("/bookings", json=booking()).status_code == 409


def test_simultaneous_requests_for_one_slot_save_only_one_booking(client):
    start_together = Barrier(2)

    def submit(user_id):
        start_together.wait(timeout=5)
        return client.post("/bookings", json=booking(user_id=user_id))

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit, user_id) for user_id in ("U1", "U4")]
        responses = [future.result(timeout=15) for future in futures]

    assert sorted(response.status_code for response in responses) == [201, 409]
    saved = user_bookings(client, "U1") + user_bookings(client, "U4")
    assert len(saved) == 1
    assert saved[0]["booking_id"] == "BK-001"
    assert saved[0]["court_id"] == "B01"
    assert client.get("/availability", params=window()).json()["available"] is False


def test_sql_like_user_input_does_not_return_other_users_records(client):
    before = user_bookings(client, "U2")

    response = client.get("/bookings", params={"user_id": "U1' OR 1=1 --"})

    assert response.status_code == 422
    assert user_bookings(client, "U2") == before
