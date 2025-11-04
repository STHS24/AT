# TraderBot Full Stack Setup Guide

Complete setup guide for the TraderBot local trading workstation with FastAPI backend, React frontend, and SQLite database.

## Architecture Overview

```
TraderBot/
├── backend/              # FastAPI backend
│   ├── app.py           # Main FastAPI application
│   ├── bot_manager.py   # Bot lifecycle management
│   ├── database.py      # SQLAlchemy database setup
│   ├── schemas.py       # Pydantic models
│   └── websocket_manager.py  # WebSocket broadcasting
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── api/         # API client
│   │   ├── hooks/       # Custom hooks (WebSocket)
│   │   └── App.jsx      # Main app component
│   └── package.json
├── strategies/          # Trading strategies (existing)
├── config/              # Configuration files
├── logs/                # Logs and database
└── main.py             # Original bot (still functional)
```

## Prerequisites

- **Python 3.12+** installed
- **Node.js 18+** and npm installed
- **MetaTrader 5** terminal installed and logged in
- Demo or live trading account

## Quick Setup (Windows)

### Option 1: Automated Setup

Run the setup script:

```bash
setup-all.bat
```

This will:
1. Create Python virtual environment
2. Install all Python dependencies
3. Install all Node.js dependencies

### Option 2: Manual Setup

Follow the detailed steps below.

## Detailed Setup Instructions

### 1. Backend Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- MetaTrader5 (MT5 API)
- FastAPI (REST API framework)
- Uvicorn (ASGI server)
- SQLAlchemy (Database ORM)
- Pydantic (Data validation)
- WebSockets (Real-time communication)
- And other utilities

#### Verify Configuration

Ensure `config/settings.json` exists with your trading parameters:

```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "deviation": 50,
  "trade_interval_seconds": 60,
  "max_concurrent_trades": 3,
  "enable_continuous_trading": true,
  "strategy_config": {
    "combination_method": "majority",
    "SimpleStrategy": {
      "enabled": true,
      "weight": 1.0,
      "params": {
        "timeframe": "M1",
        "lookback": 20
      }
    }
  },
  "risk_management": {
    "risk_percentage": 1.0,
    "daily_loss_limit": 500.0,
    "daily_profit_target": 1000.0,
    "enable_daily_limits": true
  }
}
```

### 2. Frontend Setup

#### Navigate to Frontend Directory

```bash
cd frontend
```

#### Install Node Dependencies

```bash
npm install
```

This installs:
- React (UI framework)
- Vite (Build tool)
- Tailwind CSS (Styling)
- React Query (Data fetching)
- Axios (HTTP client)
- Recharts (Charts)
- date-fns (Date utilities)

#### Return to Project Root

```bash
cd ..
```

## Running the Application

### Option 1: Using Helper Scripts (Recommended)

**Terminal 1 - Start Backend:**
```bash
start-backend.bat
```

**Terminal 2 - Start Frontend:**
```bash
start-frontend.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
# Activate virtual environment
venv\Scripts\activate

# Start FastAPI server
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --reload
```

**Terminal 2 - Frontend:**
```bash
# Navigate to frontend
cd frontend

# Start development server
npm run dev
```

## Accessing the Application

Once both servers are running:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **WebSocket**: ws://localhost:5000/ws

## Features

### Backend (FastAPI)

#### REST Endpoints

**Bot Control:**
- `POST /bot/start` - Start the trading bot
- `POST /bot/stop` - Stop the trading bot
- `GET /bot/status` - Get bot status

**Statistics:**
- `GET /stats/account` - Get MT5 account statistics
- `GET /stats/positions` - Get open positions
- `GET /stats/strategies` - Get strategy configuration

**History:**
- `GET /history/trades` - Get trade history (with pagination)

**System:**
- `GET /health` - Health check
- `GET /` - API information

#### WebSocket Events

Real-time updates for:
- **price_update** - Live price data
- **trade_execution** - Trade executions
- **log_event** - Log messages (INFO, WARNING, ERROR)
- **bot_status** - Bot status changes

### Frontend (React + Tailwind)

#### Dashboard Components

1. **Bot Control Panel**
   - Start/Stop bot
   - View bot status
   - Display uptime, trades, profit
   - Daily P&L tracking

2. **Live Price Ticker**
   - Real-time bid/ask prices
   - Spread calculation
   - Volume display

3. **Account Statistics**
   - Balance, equity, margin
   - Profit/loss
   - Margin level
   - Leverage info

4. **Open Positions**
   - List of active trades
   - Current profit/loss
   - Entry/current prices
   - SL/TP levels

5. **Trade History**
   - Paginated trade list
   - Filter by status
   - Entry/exit prices
   - Profit/loss per trade

6. **Live Logs**
   - Real-time log events
   - Color-coded by level
   - Scrollable history

## Database

The application uses SQLite for persistent storage:

- **Location**: `logs/traderbot.db`
- **Tables**:
  - `trades_api` - Trade history
  - `bot_state` - Bot state tracking

You can inspect the database using any SQLite browser:

```bash
sqlite3 logs/traderbot.db
```

## Original Bot Still Works

The original bot (`main.py`) remains fully functional:

```bash
# Single trade mode
python main.py

# Continuous trading (set in config/settings.json)
python main.py
```

## Troubleshooting

### Backend Issues

**Port 5000 already in use:**
```bash
# Change port in start command
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
```

**MT5 connection failed:**
- Ensure MetaTrader 5 is running and logged in
- Check that the account has trading permissions
- Verify symbol is available in Market Watch

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Module not found errors:**
Make sure you're in the project root directory and virtual environment is activated.

### Frontend Issues

**Port 3000 already in use:**
Vite will automatically suggest another port (usually 3001).

**WebSocket connection failed:**
- Ensure backend is running on port 5000
- Check firewall settings
- Verify WebSocket URL in `frontend/src/hooks/useWebSocket.js`

**Dependencies installation failed:**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
# Clear Vite cache
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### Common Issues

**"Cannot find module 'backend'":**
Make sure you're running uvicorn from the project root directory.

**WebSocket disconnects frequently:**
Check your network connection and firewall settings.

**Bot doesn't execute trades:**
- Verify MT5 is logged in
- Check risk management limits in config
- Review logs for error messages

## Development

### Backend Development

The backend uses FastAPI with hot-reload enabled. Changes to Python files will automatically restart the server.

**Key files:**
- `backend/app.py` - API endpoints
- `backend/bot_manager.py` - Bot control logic
- `backend/websocket_manager.py` - WebSocket broadcasting

### Frontend Development

The frontend uses Vite with hot-reload. Changes to React files will automatically update in the browser.

**Key files:**
- `frontend/src/App.jsx` - Main app component
- `frontend/src/components/` - UI components
- `frontend/src/api/client.js` - API client
- `frontend/src/hooks/useWebSocket.js` - WebSocket hook

## Production Deployment

### Backend

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn backend.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

### Frontend

```bash
# Build for production
cd frontend
npm run build

# Serve with a static server
npm install -g serve
serve -s dist -p 3000
```

## Security Notes

- **Never expose the backend to the internet** without proper authentication
- Keep `config/settings.json` secure and never commit with real credentials
- Use environment variables for sensitive data in production
- Always test on demo account first
- Set appropriate daily loss limits

## Performance Tips

- Increase `trade_interval_seconds` to reduce API calls
- Limit `max_concurrent_trades` to reduce complexity
- Monitor system resources (CPU, memory, network)
- Rotate log files regularly
- Use SSD for better database performance

## Support

- **GitHub Issues**: https://github.com/STHS24/AT/issues
- **Documentation**: See README.md and ROADMAP.md
- **API Documentation**: http://localhost:5000/docs (when backend is running)

## License

See LICENSE file for details.

