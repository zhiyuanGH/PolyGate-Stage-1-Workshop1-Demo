"""Exercise both workflows against a running local service. No LLM required."""

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BOOKING = {
    "user_id": "U1", "court_id": "B01", "date": "2026-11-05",
    "start_time": "18:00", "end_time": "19:00",
}


def call(base: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(base.rstrip("/") + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def demo(base: str) -> None:
    query = urlencode({k: v for k, v in BOOKING.items() if k != "user_id"})
    status, court = call(base, "GET", "/courts/B01")
    require(status == 200, f"Court lookup failed: {status} {court}")
    print(f"1. Court: {court['name']} at {court['location']}")

    status, availability = call(base, "GET", "/availability?" + query)
    require(status == 200 and availability["available"],
            "The example time is not available. Stop the server, run 'python -m booking_demo reset --yes', then restart.")
    print("2. B01, 5 Nov 2026, 18:00-19:00 is available.")

    status, result = call(base, "POST", "/bookings", BOOKING)
    require(status == 201 and result.get("status") == "confirmed", f"Booking failed: {status} {result}")
    booking_id = result["booking_id"]
    print("3. Created:", json.dumps(result))

    status, saved = call(base, "GET", "/bookings?user_id=U1")
    record = next((row for row in saved.get("bookings", []) if row["booking_id"] == booking_id), None)
    require(status == 200 and record == {"booking_id": booking_id, **BOOKING}, "Saved data differs from the request.")
    status, details = call(base, "GET", "/courts/" + record["court_id"])
    require(status == 200, "Could not resolve the booking location.")
    print(f"4. Check booking time and location: {record['date']}, {record['start_time']}-{record['end_time']}, {details['location']}.")

    status, rejected = call(base, "POST", "/bookings", BOOKING)
    require(status == 409, f"Expected duplicate booking rejection, got {status} {rejected}")
    _, after_conflict = call(base, "GET", "/bookings?user_id=U1")
    require(after_conflict == saved, "A rejected request changed the saved bookings.")
    print("5. Same request again: 409 Conflict; no extra booking.")

    status, invalid = call(base, "POST", "/bookings", {**BOOKING, "end_time": "17:00"})
    require(status == 422, f"Expected invalid-time rejection, got {status} {invalid}")
    _, after_invalid = call(base, "GET", "/bookings?user_id=U1")
    require(after_invalid == saved, "Invalid input changed the saved bookings.")
    status, availability = call(base, "GET", "/availability?" + query)
    require(status == 200 and availability["available"] is False, "The booked time should now be unavailable.")
    print("6. End before start: 422; saved data unchanged. All demo checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    options = parser.parse_args()
    try:
        demo(options.base_url)
    except (RuntimeError, URLError, KeyError, ValueError) as error:
        parser.exit(1, f"Demo failed: {error}\n")
