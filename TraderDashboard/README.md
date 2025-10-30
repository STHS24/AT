# TraderBot Dashboard

A real-time desktop monitoring dashboard for the TraderBot, built with Avalonia UI (.NET 8) and C#.

## Features

✅ **Real-time WebSocket Connection**
- Connects to `ws://localhost:5000`
- Automatic reconnection on failure
- Connection status indicator

✅ **Live Data Display**
- Bot status (Running, Paused, Error)
- Account balance and equity
- Current profit with percentage
- Open positions table
- Live equity curve chart

✅ **Interactive Controls**
- Start/Resume bot
- Pause bot
- Stop bot
- Dark/Light theme toggle

✅ **Activity Logging**
- Real-time log display with timestamps
- Emoji indicators for quick reading
- Auto-scrolling to newest entries
- Keeps last 100 log entries

## Requirements

- .NET 8 SDK
- Windows 10/11 (or Linux/macOS with Avalonia support)

## Installation

1. Navigate to the TraderDashboard directory:
```bash
cd TraderDashboard
```

2. Restore NuGet packages:
```bash
dotnet restore
```

3. Build the project:
```bash
dotnet build
```

## Running the Dashboard

Start the dashboard application:
```bash
dotnet run
```

The dashboard will automatically attempt to connect to `ws://localhost:5000`.

## WebSocket Data Format

The dashboard expects JSON messages in the following format:

```json
{
  "status": "running",
  "balance": 10342.50,
  "equity": 10420.33,
  "profit": 78.12,
  "positions": [
    {"symbol": "BTCUSD", "side": "long", "profit": 45.32},
    {"symbol": "ETHUSD", "side": "short", "profit": 32.80}
  ],
  "actions": ["buy BTC", "analyze ETH", "waiting..."],
  "logs": [
    "🧠 Thinking: Evaluating BTC trend",
    "📊 Action: Placed buy order on BTC",
    "💤 Waiting 30s before next action"
  ]
}
```

## Sending Commands

The dashboard can send commands to the bot via WebSocket:

- **Start/Resume**: `{"command": "resume"}`
- **Pause**: `{"command": "pause"}`
- **Stop**: `{"command": "stop"}`

## Project Structure

```
TraderDashboard/
├── TraderDashboard.csproj      # Project file with dependencies
├── Program.cs                   # Application entry point
├── App.axaml                    # Application styles
├── App.axaml.cs                 # Application code-behind
├── MainWindow.axaml             # Main window UI layout
├── MainWindow.axaml.cs          # Main window logic
├── Models/
│   ├── BotStatus.cs            # Bot status data model
│   └── Position.cs             # Position data model
└── Services/
    └── WebSocketClient.cs      # WebSocket client with auto-reconnect
```

## Dependencies

- **Avalonia 11.0.10**: Cross-platform UI framework
- **Avalonia.Desktop**: Desktop platform support
- **Avalonia.Themes.Fluent**: Modern Fluent theme
- **Avalonia.ReactiveUI**: Reactive UI extensions
- **LiveChartsCore.SkiaSharpView.Avalonia 2.0.0-rc2**: Live charting library
- **System.Net.WebSockets.Client**: WebSocket client
- **System.Text.Json 8.0.5**: JSON serialization

## UI Components

### Header Section
- Status indicator with color coding (Green=Running, Orange=Paused, Red=Error, Gray=Disconnected)
- Large display of Balance, Equity, and Profit
- Profit percentage with color coding (Green=positive, Red=negative)

### Main Section
- **Left Panel**: Table of open positions showing Symbol, Side (LONG/SHORT), and Profit
- **Right Panel**: Live equity curve chart with smooth line rendering

### Bottom Section
- Control buttons (Start, Pause, Stop, Theme Toggle)
- Scrollable activity log with timestamps and emoji indicators

## Troubleshooting

### Connection Issues
- Ensure the WebSocket server is running on `ws://localhost:5000`
- Check firewall settings
- Look for connection status messages in the activity log

### Build Issues
- Ensure .NET 8 SDK is installed: `dotnet --version`
- Clear build artifacts: `dotnet clean`
- Restore packages: `dotnet restore`

### Display Issues
- Try toggling between Dark and Light themes
- Resize the window if components are not visible
- Check that all NuGet packages are properly restored

## Testing

To test the dashboard without the actual bot, you can use the included test server (see `test_websocket_server.py` in the parent directory).

## License

Part of the TraderBot project.

