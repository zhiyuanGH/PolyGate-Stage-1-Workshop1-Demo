# API Design: Badminton Court Booking

This document describes the workshop sample's business logic and API contract. All courts, users and bookings are synthetic. The routes and fields are our teaching design, not a published PolyU API schema.

## Business tasks and shared APIs

| Business task | What the user wants | API calls, in order |
|---|---|---|
| Book a badminton court | Reserve a chosen court for a date and time. | Get court details → check availability → create a booking. |
| Check booking time and location | Find when and where an existing booking takes place. | Get the user's bookings → get details of the court in each booking. |

The tasks share **Get court details**. Implement that capability once. A booking record contains its date and time; the court record supplies its name and location.

| Capability | Endpoint |
|---|---|
| Get court details | `GET /courts/{court_id}` |
| Check availability | `GET /availability` |
| Create a booking | `POST /bookings` |
| Get a user's bookings | `GET /bookings?user_id=U1` |

Base URL when running locally: `http://127.0.0.1:8000`.

## Shared rules

- Dates use a valid calendar date in `YYYY-MM-DD` format, such as `2026-11-05`.
- Times use 24-hour `HH:MM` format, such as `18:00`. Seconds are not part of the input format.
- Dates and times refer to local Hong Kong time.
- Identifiers contain 1–64 ASCII letters, digits, underscores or hyphens, and start with a letter or digit.
- The availability and booking APIs reject unknown request-body or query fields.
- A booking starts and ends on the same date. Its end time must be later than its start time.
- Two bookings conflict when they use the same court on the same date and their time intervals overlap.
- Adjacent intervals are allowed. For example, `17:00–18:00` and `18:00–19:00` do not overlap.
- Creating a booking rechecks availability and saves the record in one transaction. A previous availability response does not reserve the court.
- Historical dates are allowed so the fixed classroom examples continue to work.

`user_id` is a mock user label. This prototype has no authentication, eligibility checks or payment processing. It does not apply additional production rules such as advance-booking windows or per-user quotas.

## 1. Get court details

**Purpose:** Identify a court and its location. Use this when choosing a court or explaining where an existing booking will take place.

**Request:** `GET /courts/{court_id}`

| Input | Where | Meaning |
|---|---|---|
| `court_id` | URL path | The court to retrieve, such as `B01`. |

**Output:** `200 OK` with `court_id`, `name` and `location`.

**Rule:** Return `404 Not Found` if the court does not exist.

Example:

```http
GET /courts/B01
```

```json
{
  "court_id": "B01",
  "name": "Badminton Court 1",
  "location": "Demo Hall"
}
```

## 2. Check availability

**Purpose:** Find out whether a court is free for the requested date and time. This call reads existing bookings without creating a new one.

**Request:** `GET /availability`

All four query parameters are required:

| Input | Example | Meaning |
|---|---|---|
| `court_id` | `B01` | The court to check. |
| `date` | `2026-11-05` | The booking date. |
| `start_time` | `18:00` | The start of the requested interval. |
| `end_time` | `19:00` | The end of the requested interval. |

**Output:** `200 OK` with the requested court, date and times, plus `available` set to `true` or `false`.

**Rules:** Apply the shared date, time and overlap rules. Return `404 Not Found` for an unknown court or `422 Unprocessable Entity` for invalid input. An occupied interval is a successful query with `available: false`, not a `409` response.

Example on a fresh database:

```http
GET /availability?court_id=B01&date=2026-11-05&start_time=18:00&end_time=19:00
```

```json
{
  "court_id": "B01",
  "date": "2026-11-05",
  "start_time": "18:00",
  "end_time": "19:00",
  "available": true
}
```

## 3. Create a booking

**Purpose:** Reserve a court for a user at the chosen date and time, then return the booking identifier and confirmation status.

**Request:** `POST /bookings` with `Content-Type: application/json`.

All five body fields are required:

| Input | Example | Meaning |
|---|---|---|
| `user_id` | `U1` | The mock user making the booking. |
| `court_id` | `B01` | The court to reserve. |
| `date` | `2026-11-05` | The booking date. |
| `start_time` | `18:00` | The start of the booking. |
| `end_time` | `19:00` | The end of the booking. |

**Output:** `201 Created` with `booking_id` and `status: "confirmed"`.

**Rules:** Check that the court exists and the inputs are valid. Recheck for an overlapping booking inside the same transaction that saves the new record. A conflict returns `409 Conflict` and saves no new booking. Unknown courts return `404 Not Found`; invalid inputs return `422 Unprocessable Entity`.

Example request:

```http
POST /bookings
Content-Type: application/json

{
  "user_id": "U1",
  "court_id": "B01",
  "date": "2026-11-05",
  "start_time": "18:00",
  "end_time": "19:00"
}
```

On a fresh database, the response is:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "booking_id": "BK-001",
  "status": "confirmed"
}
```

The identifier above is the first new booking in the seeded demo. Callers should use the returned identifier rather than assume a particular value for later bookings.

## 4. Get a user's bookings

**Purpose:** Retrieve a user's saved booking dates, times and court identifiers. To answer where a booking takes place, retrieve the corresponding court details afterwards.

**Request:** `GET /bookings?user_id=U1`

| Input | Where | Meaning |
|---|---|---|
| `user_id` | Query parameter | The mock user whose bookings to retrieve. Required. |

**Output:** `200 OK` with a `bookings` list. Each record contains `booking_id`, `user_id`, `court_id`, `date`, `start_time` and `end_time`.

**Rules:** Return only records for the requested user. If there are none, return `{"bookings": []}`. Missing or invalid input returns `422 Unprocessable Entity`.

After creating the example booking:

```http
GET /bookings?user_id=U1
```

```json
{
  "bookings": [
    {
      "booking_id": "BK-001",
      "user_id": "U1",
      "court_id": "B01",
      "date": "2026-11-05",
      "start_time": "18:00",
      "end_time": "19:00"
    }
  ]
}
```

Then call `GET /courts/B01` to obtain the court's name and location. This task can start from any saved booking; creating a booking is not part of the enquiry itself.

## Mock records and checks

The service loads initial records from [data/mock_data.json](../data/mock_data.json) into SQLite. The default database file is `data/bookings.sqlite3`; `POLYGATE_DB_FILE` can select another location.

The seed includes B01 and B02, with these existing bookings on `2026-11-05`:

| Booking | User | Court | Start | End |
|---|---|---|---|---|
| BK-000 | U2 | B01 | 16:00 | 17:00 |
| BK-009 | U3 | B02 | 15:00 | 16:00 |

Use this short test sequence:

| Check | Expected response | Expected saved data |
|---|---|---|
| Check B01, 18:00–19:00 on 5 November. | `200`, `available: true` on a fresh database. | No changes. |
| Create the example booking for U1. | `201`, `BK-001`, `confirmed`. | One new booking with the requested user, court, date and times. |
| Submit the same interval again. | `409 Conflict`. | No additional booking. |
| Retrieve U1's bookings and then B01's details. | `200` for both requests. | No changes. The response supplies the saved time and court location. |
| Use an end time earlier than the start time. | `422 Unprocessable Entity`. | No additional booking. |

To restore the practice records, follow the reset steps for your operating system in the [English guide](../README.md#if-you-get-stuck) or [中文指南](../START_HERE_zh.md#遇到问题怎么办).

The live script in `scripts/demo.py` uses fixed HTTP calls. It demonstrates these API workflows without an LLM. A later agent could choose and call the same APIs after understanding a user's request.

## References

- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/): using `TestClient` and pytest to check API behaviour.
- [Python 3.11 `sqlite3` documentation](https://docs.python.org/3.11/library/sqlite3.html): local database access, transaction control and parameterised queries.
