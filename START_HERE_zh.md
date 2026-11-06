# Workshop 1 快速入门

这个 demo 用模拟数据演示如何查询羽毛球场、检查空档、订场和查看预约。你可以直接在浏览器里调用 API，无需 API 密钥。

## 启动

1. 安装 **Python 3.11 或更新版本**。
2. [下载 ZIP](https://github.com/zhiyuanGH/PolyGate-Stage-1-Workshop1-Demo/archive/refs/heads/main.zip) 并完整解压，在包含 `start.ps1` 和 `start.sh` 的文件夹打开终端。
3. Windows 使用 PowerShell 运行 `.\start.ps1`，macOS 或 Linux 运行 `sh start.sh`。首次启动会联网安装依赖。
4. 等终端显示服务已启动，保持窗口打开，再进入[本机 API 页面](http://127.0.0.1:8000/docs)。结束时在终端按 **Ctrl+C**。

## 试一次查询和订场

在 API 页面展开 **GET /courts/{court_id}**，点 **Try it out**，输入 **B01**，再点 **Execute**。如果响应中显示 **Badminton Court 1** 和 **Demo Hall**，说明第一次查询成功。

接着按[请求示例](requests.http)检查 **B01 在 2026 年 11 月 5 日 18:00–19:00** 的空档，再用 **POST /bookings** 为 **U1** 订场。即使在其他日期练习，也请使用示例中的固定日期。初始数据下，第一次提交返回 **201**。重复提交会返回 **409**，表示该时段已被预订。最后用 **GET /bookings** 查询 `user_id=U1`，核对保存的预约。

## 如果遇到问题

- 网页提示“拒绝连接”时，检查启动服务的终端是否还开着，并使用终端显示的地址。
- 如果 Windows 阻止运行 PowerShell 脚本，可在同一文件夹依次运行以下命令。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m booking_demo
```

课堂练习只需从分配给你的题目中选择一个任务，与 coding agent 一起设计并实现一个 API，用模拟数据分别测试成功和拒绝两种情况。需要参考时，可以看[业务逻辑与 API 的对应关系](docs/API_DESIGN.md)。
