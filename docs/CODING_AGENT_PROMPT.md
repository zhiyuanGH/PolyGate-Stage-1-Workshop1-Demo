# Prompt for a coding agent

Read `docs/API_DESIGN.md`, `data/mock_data.json` and the implementation. This is the PolyGate Stage 1 Workshop 1 sample, using synthetic data only.

1. Explain how the two business tasks map to the four APIs. Keep **Check booking time and location** (a business task) distinct from **View my bookings** (an API). Explain why Get court details is shared.
2. Trace the U1 / B01 / 2026-11-05 / 18:00–19:00 request through input validation, conflict checking, database insertion and response.
3. Run the existing tests. Explain what is checked in the response and in saved data, including when two requests compete for the same time.
4. Before changing code, agree with me on the business behavior, API inputs, outputs and rules. Ask for actual system observations where the business behavior is unclear.
5. After an agreed change, update the API description, mock data and relevant tests together. Regenerate `openapi.json` with `python -m booking_demo export-openapi`.

Do not connect to real university services, treat `user_id` as authentication, or add an LLM integration unless explicitly requested. For a new assigned topic, start with one API that supports an observed business task.
