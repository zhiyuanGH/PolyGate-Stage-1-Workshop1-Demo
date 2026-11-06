# PolyGate Stage 1 Workshop 1 Demo

[中文快速入门](START_HERE_zh.md)

How does an agent find a free badminton court and book it for a student? This example breaks that task into three API calls: look up the court, check the time slot, and create a booking. A fourth API lets the student look up their bookings later. You can try all four in a browser using synthetic data on your own computer.

## Start the demo

Install **Python 3.11 or later**. [Download the ZIP](https://github.com/zhiyuanGH/PolyGate-Stage-1-Workshop1-Demo/archive/refs/heads/main.zip), extract it, and open a terminal in the folder containing `start.ps1` and `start.sh`.

| Your computer | Command |
| --- | --- |
| Windows (PowerShell) | `.\start.ps1` |
| macOS or Linux | `sh start.sh` |

The first launch installs the dependencies. Keep the terminal open. Once it says the server is running, open [the interactive API page](http://127.0.0.1:8000/docs). Press **Ctrl+C** in the terminal when you finish.

## Try your first API

1. On the API page, expand **GET /courts/{court_id}** and select **Try it out**.
2. Enter **B01** and select **Execute**.
3. Look under **Response body**. You should see **Badminton Court 1** at **Demo Hall**.

To try a booking, follow the [example requests in order](requests.http). They book court **B01** for mock user **U1** on **5 November 2026, 18:00–19:00**. Use this fixed date even if you run the exercise later. On fresh data, the first booking returns **201 Created**. Submitting it again returns **409 Conflict**. Use **GET /bookings** with `user_id=U1` to check how many bookings were saved.

## Try it with your assigned topic

Choose one task a student can perform in your assigned system. Work with your coding agent to describe one API, implement it with mock data, and test one successful request and one request that should be rejected.

- [API design](docs/API_DESIGN.md) explains how the two booking workflows share an API.
- [Mock data](data/mock_data.json) shows the sample courts and bookings used on first launch.
- [Coding agent prompt](docs/CODING_AGENT_PROMPT.md) gives you a starting point for your own design.
