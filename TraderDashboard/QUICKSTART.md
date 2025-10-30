# TraderBot Dashboard - Quick Start Guide

Get your dashboard up and running in 5 minutes!

---

## 🚀 Quick Start (Testing Mode)

### Step 1: Install Dependencies

```bash
# Install Python WebSocket library
pip install websockets
```

### Step 2: Start Test Server

Open a terminal and run:

```bash
# From TraderBot root directory
python test_websocket_server.py
```

You should see:
```
🚀 TraderBot Dashboard Test Server
📡 Starting WebSocket server on ws://localhost:5000
```

### Step 3: Start Dashboard

Open a **new terminal** and run:

```bash
# Navigate to dashboard directory
cd TraderDashboard

# Run the dashboard
dotnet run
```

The dashboard window will open and automatically connect!

---

## 🎮 Using the Dashboard

### What You'll See

**Header Section:**
- 🟢 Status indicator (Green = Running, Orange = Paused, Red = Error)
- 💰 Balance, Equity, and Profit displays
- 📊 Profit percentage with color coding

**Main Section:**
- 📋 **Left**: Table of open positions
- 📈 **Right**: Live equity curve chart

**Bottom Section:**
- 🎛️ Control buttons (Start, Pause, Stop, Theme Toggle)
- 📝 Activity log with timestamps

### Interactive Features

**Control Buttons:**
- Click **▶️ START** to resume trading
- Click **⏸️ PAUSE** to pause trading
- Click **⏹️ STOP** to stop trading
- Click **🌙 DARK MODE** to toggle theme

**Live Updates:**
- Equity chart updates every 2 seconds
- Positions table refreshes in real-time
- Activity log shows latest actions
- All data syncs automatically

---

## 🔧 Connecting to Your Real Bot

### Option 1: Use Integration Guide

Follow the detailed steps in `DASHBOARD_INTEGRATION.md` to integrate the WebSocket server into your `main.py`.

### Option 2: Quick Integration

1. Copy `websocket_server.py` template from integration guide
2. Add WebSocket server to your bot's main loop
3. Call `broadcast_dashboard_update()` after each trading iteration
4. Handle commands (pause/resume/stop) in your bot

---

## 📊 Data Format

The dashboard expects JSON messages like this:

```json
{
  "status": "running",
  "balance": 10342.50,
  "equity": 10420.33,
  "profit": 78.12,
  "positions": [
    {"symbol": "BTCUSD", "side": "long", "profit": 45.32}
  ],
  "actions": ["Analyzing BTCUSD", "Waiting for signal"],
  "logs": [
    "🧠 Thinking: Evaluating market conditions",
    "📊 Action: Signal detected"
  ]
}
```

---

## 🐛 Troubleshooting

### Dashboard shows "Disconnected"
**Solution:** Make sure the WebSocket server is running on port 5000.

```bash
# Check if server is running
python -c "import socket; s = socket.socket(); print('OK' if s.connect_ex(('localhost', 5000)) == 0 else 'Not running'); s.close()"
```

### Dashboard won't start
**Solution:** Check .NET installation.

```bash
# Verify .NET 8 is installed
dotnet --version
```

If not installed, download from: https://dotnet.microsoft.com/download/dotnet/8.0

### Build errors
**Solution:** Clean and rebuild.

```bash
cd TraderDashboard
dotnet clean
dotnet restore
dotnet build
```

### Port 5000 already in use
**Solution:** Change the port in both files:

1. Edit `test_websocket_server.py` line 158: `port = 5001`
2. Edit `TraderDashboard/MainWindow.axaml.cs` line 26: `"ws://localhost:5001"`

---

## 🎨 Customization

### Change Window Size

Edit `MainWindow.axaml` lines 10-11:
```xml
Width="1400"    <!-- Change from 1200 -->
Height="900"    <!-- Change from 800 -->
```

### Change Update Frequency

Edit `test_websocket_server.py` line 107:
```python
await asyncio.sleep(5)  # Update every 5 seconds instead of 2
```

### Change Chart History

Edit `MainWindow.axaml.cs` line 23:
```csharp
private readonly int _maxEquityPoints = 200;  // Show 200 points instead of 100
```

---

## 📱 Keyboard Shortcuts

- **Ctrl+C** in terminal: Stop the server/dashboard
- **Alt+F4**: Close dashboard window
- **Theme Toggle Button**: Switch between light/dark mode

---

## 🎯 Next Steps

1. ✅ Test with mock server (you just did this!)
2. 📖 Read `DASHBOARD_INTEGRATION.md` for real bot integration
3. 🔧 Customize the dashboard to your needs
4. 🚀 Deploy and monitor your trading bot!

---

## 📚 Additional Resources

- **README.md** - Full documentation
- **DASHBOARD_SUMMARY.md** - Implementation details
- **DASHBOARD_INTEGRATION.md** - Integration guide
- **test_websocket_server.py** - Test server source code

---

## 💡 Tips

- Keep the test server running while developing
- Use Dark Mode for extended monitoring sessions
- Watch the activity log for connection issues
- The dashboard auto-reconnects if the server restarts

---

## ✅ Checklist

Before connecting to your real bot:

- [ ] Test server works correctly
- [ ] Dashboard connects and displays data
- [ ] Control buttons send commands
- [ ] Theme toggle works
- [ ] Chart updates smoothly
- [ ] Positions table displays correctly
- [ ] Activity log shows messages

---

## 🆘 Need Help?

If you encounter issues:

1. Check the terminal output for error messages
2. Verify WebSocket server is running
3. Ensure .NET 8 SDK is installed
4. Try restarting both server and dashboard
5. Check firewall settings

---

## 🎉 You're Ready!

Your dashboard is now running and ready to monitor your trading bot in real-time!

**Happy Trading! 📈💰**

