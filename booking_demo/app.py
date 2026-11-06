"""Four business APIs, matching the Workshop 1 badminton example."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
import os

from fastapi import FastAPI, Path as PathParameter, Query, Request
from fastapi.responses import JSONResponse

from .models import Availability, BookingCreated, BookingRequest, Bookings, Court, TimeWindow, UserQuery
from .store import BookingConflict, DEFAULT_SEED, ROOT, Store, UnknownCourt

EXAMPLE = {
    "user_id": "U1", "court_id": "B01", "date": "2026-11-05",
    "start_time": "18:00", "end_time": "19:00",
}


def create_app(db_path: Path | None = None, seed_path: Path | None = None) -> FastAPI:
    path = db_path if db_path is not None else Path(os.getenv("POLYGATE_DB_FILE", ROOT / "data" / "bookings.sqlite3"))
    store = Store(Path(path), Path(seed_path) if seed_path is not None else DEFAULT_SEED)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        store.initialize()
        yield

    application = FastAPI(
        title="PolyGate Workshop 1 — Badminton Booking Mock APIs",
        version="1.0.0",
        description=(
            "A standalone teaching sample with synthetic data. All dates and times are local to Hong Kong. "
            "Use U1 as a mock user; user_id is not authentication. No real PolyU system or LLM is contacted. "
            "Start with GET /courts/B01, check availability, create a booking, then view U1's bookings."
        ),
        lifespan=lifespan,
    )
    application.state.store = store

    @application.exception_handler(UnknownCourt)
    async def unknown_court(_request: Request, error: UnknownCourt):
        return JSONResponse(status_code=404, content={"detail": f"Court {error.args[0]} does not exist."})

    @application.exception_handler(BookingConflict)
    async def conflict(_request: Request, _error: BookingConflict):
        return JSONResponse(status_code=409, content={"detail": "This court is already booked for the requested time."})

    @application.get(
        "/courts/{court_id}", response_model=Court, operation_id="get_court_details",
        summary="Get court details", tags=["Courts"],
        description="Find the court name and location. Shared by both business workflows.",
        responses={404: {"description": "The court does not exist."}},
    )
    def get_court(court_id: Annotated[str, PathParameter(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$", max_length=64)]):
        return store.court(court_id)

    @application.get(
        "/availability", response_model=Availability, operation_id="check_availability",
        summary="Check availability", tags=["Bookings"],
        description=(
            "Check one court, date and time range. This query does not reserve the court. "
            "A booking ending exactly at the requested start time does not overlap."
        ),
        responses={404: {"description": "The court does not exist."}},
    )
    def get_availability(window: Annotated[TimeWindow, Query()]):
        return {**window.model_dump(), "available": store.available(window)}

    @application.post(
        "/bookings", response_model=BookingCreated, status_code=201, operation_id="create_booking",
        summary="Create a booking", tags=["Bookings"],
        description=(
            "Reserve a court for the requested time. All five fields are required. "
            "Availability is checked again inside the write transaction. On conflict, no booking is added. "
            "For a freshly initialized sample, the slide example creates BK-001."
        ),
        responses={404: {"description": "The court does not exist."}, 409: {"description": "An existing booking overlaps."}},
        openapi_extra={"requestBody": {"content": {"application/json": {"example": EXAMPLE}}}},
    )
    def post_booking(booking: BookingRequest):
        return {"booking_id": store.create_booking(booking), "status": "confirmed"}

    @application.get(
        "/bookings", response_model=Bookings, operation_id="view_my_bookings",
        summary="View my bookings", tags=["Bookings"],
        description=(
            "Return bookings for a synthetic user. An unused user ID returns an empty list. "
            "To check booking time and location, read these records then call Get court details."
        ),
    )
    def get_bookings(query: Annotated[UserQuery, Query()]):
        return {"bookings": store.bookings_for(query.user_id)}

    return application


app = create_app()
