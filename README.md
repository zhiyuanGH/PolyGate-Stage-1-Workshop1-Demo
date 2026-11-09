# PolyGate Stage 1 Workshop 1 · Badminton court booking demo

Imagine a student asks, “Can I book court B01 from 6 to 7 pm?” You’ll use a browser to make the same calls an agent could make: find the court, check the time, book it, and look up the reservation. Everything runs on your computer with fictional records. You can do the exercise without writing code or signing in.

## 1. Open the demo on your computer

Use the ZIP attached to the workshop email or [download the ZIP from GitHub](https://github.com/zhiyuanGH/PolyGate-Stage-1-Workshop1-Demo/archive/refs/heads/main.zip). Extract it completely. Open the folder that contains this README and the files `start.ps1` and `start.sh`.

You’ll need **Python 3.11 or later** and an internet connection for the first launch. Follow the row for your computer. Type each command and press **Enter**.

| Computer | Open a terminal in the extracted folder | Check Python | Start the demo |
| --- | --- | --- | --- |
| Windows | In File Explorer, click the address bar, type `powershell`, and press Enter. | `python --version` | `.\start.ps1` |
| macOS | Open Terminal. Type `cd ` (including the space), drag the extracted folder into the window, and press Return. | `python3 --version` | `sh start.sh` |
| Linux | Right-click inside the extracted folder and select **Open in Terminal**, if available. | `python3 --version` | `sh start.sh` |

If the version command fails or shows a version below 3.11, install [Python](https://www.python.org/downloads/), then reopen the terminal in the same folder.

Wait until you see **Uvicorn running**. Leave that window open and visit **[the demo API page](http://127.0.0.1:8000/docs)** in a browser on the same computer. Keep the guide open alongside it.

## 2. Make a booking and check what was saved

On the API page, click a row to expand it, then click **Try it out**. Fill in the values below and click **Execute**. Under **Server response**, **Code** tells you what happened and **Response body** shows the result. Use the example date even if you’re doing the exercise later.

### A. Where is court B01?

Open **Get court details** (`GET /courts/{court_id}`). Enter `B01` for `court_id` and click **Execute**. Look for **Badminton Court 1** and **Demo Hall** in the response.

### B. Is it free from 6 to 7 pm?

Open **Check availability** (`GET /availability`) and enter these four values.

| Field | Value |
| --- | --- |
| `court_id` | `B01` |
| `date` | `2026-11-05` |
| `start_time` | `18:00` |
| `end_time` | `19:00` |

Click **Execute**. On a fresh copy, you’ll see `"available": true`. Checking a time slot leaves it free until someone books it.

### C. Book the court for student U1

Open **Create a booking** (`POST /bookings`) and click **Try it out**. Replace **all** the text in the **Request body** box with this example, then click **Execute** once.

```json
{
  "user_id": "U1",
  "court_id": "B01",
  "date": "2026-11-05",
  "start_time": "18:00",
  "end_time": "19:00"
}
```

**201** means the booking was saved. The response includes a `booking_id` and the status `confirmed`. Now click **Execute** again with exactly the same details. **409** is the expected result: the court is already booked for that time.

### D. Did the second click create a second booking?

Open **View my bookings** (`GET /bookings`). Enter `U1` for `user_id` and click **Execute**. After the steps above on fresh data, you should find **one booking** for B01, 18:00–19:00. Its ID matches the one returned in C. Repeat B to see that `available` is now `false`.

When you finish, press **Ctrl+C** in the terminal to stop the demo.

## 3. Apply this to your workshop topic

Choose **one task** you have observed in your assigned system. Write down what the student wants to do, what information they need to provide, and what a successful result looks like. Work with your coding agent to implement **one API** with mock data. Try one request that should succeed and one that should be rejected. Check both the response and what was saved, as you did in C and D.

- [API design notes](docs/API_DESIGN.md) show how two student tasks share the court lookup API.
- [Mock data](data/mock_data.json) shows the courts and bookings the demo starts with.
- [Coding agent prompt](docs/CODING_AGENT_PROMPT.md) helps you explore the sample with your agent.

## If you get stuck

- **The browser says “connection refused”.** Return to the terminal, start the demo if it has stopped, and wait for **Uvicorn running** before refreshing the page.
- **Windows says scripts are disabled.** In the same PowerShell window, run the following commands one line at a time. Then open the demo API page as above.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m booking_demo
```

- **The first booking already returns 409.** Bookings persist when you close the demo. To repeat the exercise from the beginning, stop it with **Ctrl+C** and run the reset command below. This removes bookings you added and restores the original practice records. Then start the demo again using section 1.

| Windows (PowerShell) | macOS or Linux |
| --- | --- |
| `.\.venv\Scripts\python.exe -m booking_demo reset --yes` | `.venv/bin/python -m booking_demo reset --yes` |
