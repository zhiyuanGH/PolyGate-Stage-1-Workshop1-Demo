"""Run from the sample directory: python -m booking_demo."""

import argparse
import json
from pathlib import Path

from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="PolyGate local classroom mock API")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "reset", "export-openapi"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--yes", action="store_true", help="Confirm restoring the local database to its seed data")
    parser.add_argument("--output", type=Path, default=Path("openapi.json"))
    args = parser.parse_args()
    application = create_app()
    if args.command == "reset":
        if not args.yes:
            parser.error("Reset removes locally created mock bookings. Add --yes to confirm.")
        application.state.store.reset()
        print(f"Seed data restored: {application.state.store.db_path}")
    elif args.command == "export-openapi":
        args.output.write_text(json.dumps(application.openapi(), indent=2), encoding="utf-8")
        print(f"OpenAPI specification: {args.output.resolve()}")
    else:
        if not 1 <= args.port <= 65535:
            parser.error("Port must be between 1 and 65535")
        import uvicorn
        print(f"Interactive API documentation: http://{args.host}:{args.port}/docs")
        uvicorn.run(application, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
