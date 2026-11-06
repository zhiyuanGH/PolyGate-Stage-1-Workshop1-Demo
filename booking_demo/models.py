"""The agreed inputs and outputs, kept separate from HTTP and storage."""

from datetime import date as CalendarDate
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[
    str, Field(strict=True, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
]
Day = Annotated[str, Field(strict=True, pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")]
ClockTime = Annotated[str, Field(strict=True, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimeWindow(StrictModel):
    court_id: Identifier = Field(description="Court identifier, for example B01.")
    date: Day = Field(description="Local calendar date, YYYY-MM-DD (Hong Kong time).")
    start_time: ClockTime = Field(description="Start time, HH:MM, inclusive.")
    end_time: ClockTime = Field(description="End time, HH:MM, exclusive, on the same date.")

    @field_validator("date")
    @classmethod
    def real_calendar_date(cls, value: str) -> str:
        CalendarDate.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time on the same date")
        return self


class BookingRequest(TimeWindow):
    user_id: Identifier = Field(description="Synthetic classroom identity, e.g. U1; not authentication.")


class Booking(BookingRequest):
    booking_id: Identifier


class Court(StrictModel):
    court_id: Identifier
    name: Annotated[str, Field(strict=True, min_length=1, max_length=120)]
    location: Annotated[str, Field(strict=True, min_length=1, max_length=120)]


class Availability(TimeWindow):
    available: bool


class BookingCreated(StrictModel):
    booking_id: Identifier
    status: Literal["confirmed"] = "confirmed"


class UserQuery(StrictModel):
    user_id: Identifier


class Bookings(StrictModel):
    bookings: list[Booking]


class SeedData(StrictModel):
    courts: list[Court]
    bookings: list[Booking]
