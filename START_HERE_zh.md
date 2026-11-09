# PolyGate Stage 1 Workshop 1 · 羽毛球订场示例

[English guide](README.md)

假设有学生问：“我想订晚上六点到七点的 B01 羽毛球场，可以吗？”你会在浏览器里亲手做四件事：查场地、查空档、订场、查预约。以后，agent 也可以调用这四个 API 帮学生完成同样的事。示例使用虚构数据，在你自己的电脑上运行，无需编程或登录账号。

## 1. 在自己的电脑上打开示例

将邮件里的 ZIP **完整解压**，也可以[从 GitHub 下载](https://github.com/zhiyuanGH/PolyGate-Stage-1-Workshop1-Demo/archive/refs/heads/main.zip)。打开解压后的文件夹，直到能看到 `README.md`、`start.ps1` 和 `start.sh` 这三个文件。

准备好 **Python 3.11 或以上版本**，首次启动时保持联网。按下表找到自己的系统，每输入一条命令就按一次回车。

| 电脑系统 | 在解压后的文件夹打开终端 | 检查 Python 版本 | 启动示例 |
| --- | --- | --- | --- |
| Windows | 在文件资源管理器里点击上方地址栏，输入 `powershell` 并回车。 | `python --version` | `.\start.ps1` |
| macOS | 打开“终端”，输入 `cd `（保留末尾的空格），把解压后的文件夹拖进终端，再按回车。 | `python3 --version` | `sh start.sh` |
| Linux | 在文件夹空白处点右键，若菜单中有“在终端打开”，点击该选项。 | `python3 --version` | `sh start.sh` |

如果查不到版本，或版本低于 3.11，请先[安装 Python](https://www.python.org/downloads/)，然后回到同一文件夹重新打开终端。

等终端出现 **Uvicorn running**，保持这个窗口开着，在**同一台电脑**的浏览器打开 **[API 练习页面](http://127.0.0.1:8000/docs)**。你可以一边看这份指南，一边操作。

## 2. 订一次场，看看系统存下了什么

在练习页面点击对应的一行，展开后点 **Try it out**。填好下面的值后点 **Execute**（执行）。在 **Server response** 区域，**Code** 是结果编号，**Response body** 是系统返回的内容。即使今天已经过了示例日期，也请照填。

### A. B01 球场在哪里？

展开 **Get court details**（`GET /courts/{court_id}`），在 `court_id` 填入 `B01`，点 **Execute**。如果看到 **Badminton Court 1** 和 **Demo Hall**，说明你已经查到了球场名称和地点。

### B. 晚上六点到七点有空场吗？

展开 **Check availability**（`GET /availability`），填写下面四项。

| 输入框 | 填入的值 |
| --- | --- |
| `court_id`（球场编号） | `B01` |
| `date`（日期） | `2026-11-05` |
| `start_time`（开始时间） | `18:00` |
| `end_time`（结束时间） | `19:00` |

点 **Execute**。第一次运行时，你会看到 `"available": true`，表示这个时段可以预订。查空档只会读取数据，球场仍然是空的。

### C. 帮学生 U1 订下这个时段

展开 **Create a booking**（`POST /bookings`），点 **Try it out**。把 **Request body** 输入框里的原有内容**全部替换**成下面这段，然后点一次 **Execute**。

```json
{
  "user_id": "U1",
  "court_id": "B01",
  "date": "2026-11-05",
  "start_time": "18:00",
  "end_time": "19:00"
}
```

返回 **201** 表示预约已保存。你会看到一个预约编号 `booking_id`，以及状态 `confirmed`（已确认）。现在保持内容不变，再点一次 **Execute**。这次应该返回 **409**，表示这个球场的同一时段已经有人订了。

### D. 点了两次，会不会留下两笔预约？

展开 **View my bookings**（`GET /bookings`），在 `user_id` 填入 `U1`，点 **Execute**。如果从初始数据开始操作，你会看到 B01 在 18:00–19:00 **只有一笔预约**，编号与 C 中返回的一致。再做一次 B，这次 `available` 会变成 `false`。

练习结束后，回到终端按 **Ctrl+C** 停止服务。

## 3. 应用到你分配到的题目

从你实际用过的系统中选**一个任务**。用一句话写清楚学生想做什么，再列出学生需要提供的信息，以及成功时应看到的结果。和 coding agent 一起用模拟数据实现其中**一个 API**。试一次应该成功的请求，再试一次应该被拒绝的请求。像 C 和 D 那样，同时检查返回结果和实际保存的记录。

- [API 设计说明](docs/API_DESIGN.md)展示了“订场”和“查预约的时间地点”怎样共用同一个场地查询 API。
- [初始模拟数据](data/mock_data.json)列出了练习开始前已有的球场和预约。
- [Coding agent 提示词](docs/CODING_AGENT_PROMPT.md)可以用来和你的 agent 讨论这个样例。

## 遇到问题怎么办？

- **浏览器显示“拒绝连接”。** 回到终端检查服务是否在运行。如果已经停止，重新启动，等看到 **Uvicorn running** 再刷新网页。
- **Windows 提示禁止运行脚本。** 在同一个 PowerShell 窗口，逐行执行下面三条命令，再按上文打开 API 练习页面。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m booking_demo
```

- **第一次订场就返回 409。** 关闭服务后，之前的预约仍会保留。如果想从头练习，先按 **Ctrl+C** 停止服务，再按下表运行重置命令。这会清除你在练习中新增的预约，并恢复最初的示例数据。然后按第 1 节重新启动。

| Windows（PowerShell） | macOS 或 Linux |
| --- | --- |
| `.\.venv\Scripts\python.exe -m booking_demo reset --yes` | `.venv/bin/python -m booking_demo reset --yes` |
