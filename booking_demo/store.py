"""Two SQLite tables. A booking check and insert form one transaction."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from .models import BookingRequest, SeedData, TimeWindow

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEED = ROOT / "data" / "mock_data.json"
APPLICATION_ID = 0x50474D31  # PGM1: only reset databases created by this sample.


class UnknownCourt(Exception):
    pass


class BookingConflict(Exception):
    pass


class Store:
    def __init__(self, db_path: Path, seed_path: Path = DEFAULT_SEED):
        self.db_path = Path(db_path).resolve()
        self.seed_path = Path(seed_path).resolve()

    @contextmanager
    def connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            if write:
                # Reserve the writer before checking availability. Two concurrent
                # requests cannot both see an empty slot and then both insert.
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            if write:
                connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as connection:
            tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            app_id = connection.execute("PRAGMA application_id").fetchone()[0]
            if tables:
                if app_id != APPLICATION_ID or not {"courts", "bookings"}.issubset(tables):
                    raise RuntimeError("This database was not created by the workshop sample. Choose another path.")
                return  # Preserve bookings across restarts; never silently reseed.
            connection.execute("""CREATE TABLE courts (
                court_id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL
            )""")
            connection.execute("""CREATE TABLE bookings (
                booking_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                court_id TEXT NOT NULL REFERENCES courts(court_id),
                date TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL,
                CHECK (end_time > start_time)
            )""")
            connection.execute("CREATE INDEX booking_slot ON bookings(court_id, date, start_time, end_time)")
            connection.execute("CREATE INDEX booking_user ON bookings(user_id)")
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            connection.execute("PRAGMA user_version = 1")
            self._insert_seed(connection)

    def _insert_seed(self, connection: sqlite3.Connection) -> None:
        seed = SeedData.model_validate_json(self.seed_path.read_text(encoding="utf-8"))
        for court in seed.courts:
            connection.execute(
                "INSERT INTO courts VALUES (:court_id, :name, :location)", court.model_dump()
            )
        for booking in seed.bookings:
            self._require_court(connection, booking.court_id)
            if self._overlap(connection, booking):
                raise ValueError("Seed data contains overlapping bookings")
            self._insert_booking(connection, booking.model_dump())

    def reset(self) -> None:
        """Explicit local reset; no reset HTTP endpoint is exposed."""
        self.initialize()
        with self.connection(write=True) as connection:
            if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
                raise RuntimeError("Refusing to reset an unrelated database")
            connection.execute("DELETE FROM bookings")
            connection.execute("DELETE FROM courts")
            self._insert_seed(connection)

    @staticmethod
    def _require_court(connection: sqlite3.Connection, court_id: str) -> dict:
        row = connection.execute("SELECT * FROM courts WHERE court_id = ?", (court_id,)).fetchone()
        if row is None:
            raise UnknownCourt(court_id)
        return dict(row)

    @staticmethod
    def _overlap(connection: sqlite3.Connection, window: TimeWindow) -> bool:
        # [start, end): an earlier booking ending at 18:00 does not conflict
        # with a new booking starting at 18:00.
        return connection.execute(
            """SELECT 1 FROM bookings
               WHERE court_id = ? AND date = ? AND start_time < ? AND end_time > ?
               LIMIT 1""",
            (window.court_id, window.date, window.end_time, window.start_time),
        ).fetchone() is not None

    @staticmethod
    def _insert_booking(connection: sqlite3.Connection, record: dict) -> None:
        connection.execute(
            """INSERT INTO bookings (booking_id, user_id, court_id, date, start_time, end_time)
               VALUES (:booking_id, :user_id, :court_id, :date, :start_time, :end_time)""",
            record,
        )

    def court(self, court_id: str) -> dict:
        with self.connection() as connection:
            return self._require_court(connection, court_id)

    def available(self, window: TimeWindow) -> bool:
        with self.connection() as connection:
            self._require_court(connection, window.court_id)
            return not self._overlap(connection, window)

    def create_booking(self, request: BookingRequest) -> str:
        with self.connection(write=True) as connection:
            self._require_court(connection, request.court_id)
            if self._overlap(connection, request):
                raise BookingConflict
            # Classroom-friendly IDs match the slides even though BK-009 is
            # already in the seed. The transaction also protects ID allocation.
            number = 1
            while connection.execute(
                "SELECT 1 FROM bookings WHERE booking_id = ?", (f"BK-{number:03d}",)
            ).fetchone():
                number += 1
            booking_id = f"BK-{number:03d}"
            self._insert_booking(connection, {"booking_id": booking_id, **request.model_dump()})
            return booking_id

    def bookings_for(self, user_id: str) -> list[dict]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM bookings WHERE user_id = ? ORDER BY date, start_time, booking_id",
                (user_id,),
            )]
