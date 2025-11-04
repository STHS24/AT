# TraderBot Architecture & Workflow Analysis

## 🏗️ System Architecture Overview

The TraderBot system consists of **two independent servers** that communicate via REST API and WebSocket:

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                     http://localhost:3000                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    FRONTEND SERVER                               │
│                  React + Vite (Port 3000)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  App.jsx (Main Dashboard)                                │  │
│  │    ├─ useWebSocket Hook (Real-time)                      │  │
│  │    ├─ BotControl Component (Start/Stop)                  │  │
│  │    ├─ PriceTicker Component (Live Prices)                │  │
│  │    ├─ AccountStats Component (Account Info)              │  │
│  │    ├─ OpenPositions Component (Active Trades)            │  │
│  │    ├─ TradeHistory Component (Past Trades)               │  │
│  │    └─ LogViewer Component (Live Logs)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API (axios)
                         │ WebSocket (ws://)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    BACKEND SERVER                                │
│                FastAPI + Uvicorn (Port 5000)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  app.py (FastAPI Application)                            │  │
│  │    ├─ REST Endpoints (/bot/*, /stats/*, /history/*)     │  │
│  │    └─ WebSocket Endpoint (/ws)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  bot_manager.py (Bot Lifecycle)                          │  │
│  │    ├─ Start/Stop Bot                                     │  │
│  │    ├─ Bot Thread (Separate Thread)                       │  │
│  │    └─ Trading Loop                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  websocket_manager.py (Broadcasting)                     │  │
│  │    └─ Broadcast to All Connected Clients                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  database.py (SQLite + SQLAlchemy)                       │  │
│  │    └─ Store Trades & Bot State                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ MT5 Python API
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   METATRADER 5 TERMINAL                          │
│                    (Trading Platform)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Market Data (Prices, Ticks)                           │  │
│  │  - Account Information                                    │  │
│  │  - Order Execution                                        │  │
│  │  - Position Management                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow: User Starts Bot

### Step 1: User Clicks "Start Bot" Button

**Location:** `frontend/src/components/BotControl.jsx`

```javascript
// User clicks button
handleStart() → startMutation.mutate({})
```

**What happens:**
- React Query mutation triggered
- Calls `botAPI.start()` from API client

---

### Step 2: Frontend Sends HTTP POST Request

**Location:** `frontend/src/api/client.js`

```javascript
botAPI.start(data) → axios.post('/bot/start', data)
```

**HTTP Request:**
```
POST http://localhost:5000/bot/start
Content-Type: application/json
Body: { "symbol": null, "trade_interval": null }
```

---

### Step 3: Backend Receives Request

**Location:** `backend/app.py` (Line 63-83)

```python
@app.post("/bot/start")
async def start_bot(request: BotStartRequest):
    result = bot_manager.start(
        symbol=request.symbol,
        trade_interval=request.trade_interval
    )
```

**What happens:**
- FastAPI endpoint receives request
- Validates request with Pydantic schema
- Calls `bot_manager.start()`

---

### Step 4: Bot Manager Initializes Bot

**Location:** `backend/bot_manager.py` (Line 224-276)

```python
def start(self, symbol, trade_interval):
    # 1. Initialize MT5 connection
    self._initialize_mt5()
    
    # 2. Prepare trading symbol
    self._prepare_symbol(symbol)
    
    # 3. Initialize strategies from config
    self.strategy_manager = self._initialize_strategies()
    
    # 4. Initialize risk manager
    self.risk_manager = RiskManager(self.config)
    
    # 5. Initialize trade logger
    self.trade_logger = TradeLogger()
    
    # 6. Start bot thread
    self.bot_thread = threading.Thread(
        target=self._bot_loop,
        args=(symbol, trade_interval),
        daemon=True
    )
    self.bot_thread.start()
```

**What happens:**
1. Connects to MetaTrader 5
2. Loads strategies from `config/settings.json`
3. Initializes risk management
4. **Starts bot in separate thread** (non-blocking!)
5. Returns success response

---

### Step 5: Bot Thread Starts Trading Loop

**Location:** `backend/bot_manager.py` (Line 200-222)

```python
def _bot_loop(self, symbol, interval):
    while not self._stop_flag:
        # 1. Perform trading iteration
        self._trading_iteration(symbol)
        
        # 2. Broadcast price update via WebSocket
        asyncio.run(self._broadcast_price_update(symbol))
        
        # 3. Sleep for interval (e.g., 60 seconds)
        time.sleep(interval)
```

**What happens:**
- Runs continuously in background thread
- Every `interval` seconds (default 60s):
  - Checks risk limits
  - Gets strategy signals
  - Executes trades if conditions met
  - Broadcasts updates via WebSocket

---

### Step 6: Trading Iteration Executes

**Location:** `backend/bot_manager.py` (Line 163-198)

```python
def _trading_iteration(self, symbol):
    # 1. Check risk limits
    daily_pnl = self.risk_manager.get_daily_pnl()
    can_trade, reason = self.risk_manager.can_trade()
    
    # 2. Broadcast bot status via WebSocket
    asyncio.run(ws_manager.broadcast_bot_status(...))
    
    # 3. Get strategy signal
    action = self.strategy_manager.generate_combined_signal(symbol)
    
    # 4. Check if can open new trade
    if self._can_open_new_trade():
        # 5. Execute trade (calls existing logic)
        # 6. Broadcast trade execution via WebSocket
        asyncio.run(ws_manager.broadcast_trade_execution(...))
```

**What happens:**
1. Checks daily P&L limits
2. Gets combined signal from all strategies
3. Executes trade if signal is BUY/SELL
4. Broadcasts updates to all connected clients

---

### Step 7: WebSocket Manager Broadcasts Updates

**Location:** `backend/websocket_manager.py` (Line 44-73)

```python
async def broadcast(self, message):
    # Convert message to JSON
    json_message = json.dumps(message)
    
    # Send to ALL connected WebSocket clients
    for connection in self.active_connections:
        await connection.send_text(json_message)
```

**Message Types:**
- `price_update` - Live price data
- `trade_execution` - Trade executed
- `log_event` - Log message
- `bot_status` - Bot status change

---

### Step 8: Frontend Receives WebSocket Message

**Location:** `frontend/src/hooks/useWebSocket.js` (Line 34-63)

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    // Route message based on type
    switch (message.type) {
        case 'price_update':
            setPriceData(message.data);
            break;
        
        case 'trade_execution':
            setTradeExecutions(prev => [message.data, ...prev]);
            break;
        
        case 'log_event':
            setLogEvents(prev => [message.data, ...prev]);
            break;
        
        case 'bot_status':
            setBotStatus(message.data);
            break;
    }
}
```

**What happens:**
- WebSocket receives JSON message
- Parses message and routes by type
- Updates React state
- Triggers UI re-render

---

### Step 9: React Components Update UI

**Location:** `frontend/src/App.jsx` (Line 14-21)

```javascript
const { priceData, tradeExecutions, logEvents, botStatus } = useWebSocket();

// Components receive data as props
<PriceTicker priceData={priceData} />
<LogViewer logEvents={logEvents} />
<TradeHistory />
```

**What happens:**
- Components receive updated data
- React re-renders affected components
- User sees live updates in browser

---

## 📊 Data Flow Diagram

```
USER ACTION (Click "Start Bot")
    ↓
FRONTEND (BotControl.jsx)
    ↓ HTTP POST /bot/start
BACKEND API (app.py)
    ↓ Call bot_manager.start()
BOT MANAGER (bot_manager.py)
    ↓ Initialize MT5, Strategies, Risk Manager
    ↓ Start bot_thread (separate thread)
BOT THREAD (_bot_loop)
    ↓ Every 60 seconds
    ├─→ Check risk limits
    ├─→ Get strategy signals
    ├─→ Execute trades
    └─→ Broadcast updates
         ↓
WEBSOCKET MANAGER (websocket_manager.py)
    ↓ Broadcast to all clients
FRONTEND WEBSOCKET (useWebSocket.js)
    ↓ Receive message
    ↓ Update React state
REACT COMPONENTS
    ↓ Re-render UI
USER SEES UPDATE
```

---

## 🔌 Communication Channels

### 1. REST API (HTTP)

**Purpose:** Commands and queries

**Direction:** Frontend → Backend

**Examples:**
- `POST /bot/start` - Start bot
- `POST /bot/stop` - Stop bot
- `GET /bot/status` - Get status
- `GET /stats/account` - Get account info
- `GET /history/trades` - Get trade history

**Technology:** Axios (frontend) → FastAPI (backend)

---

### 2. WebSocket (ws://)

**Purpose:** Real-time updates

**Direction:** Backend → Frontend (broadcast)

**Examples:**
- Price updates every iteration
- Trade executions when trades happen
- Log events as they occur
- Bot status changes

**Technology:** Native WebSocket API (frontend) → FastAPI WebSocket (backend)

---

### 3. MetaTrader 5 API

**Purpose:** Trading operations

**Direction:** Backend → MT5 Terminal

**Examples:**
- Get price data
- Get account info
- Execute orders
- Get positions

**Technology:** MetaTrader5 Python library

---

## 🧵 Threading Model

### Backend Threading

```
Main Thread (FastAPI/Uvicorn)
├─ HTTP Request Handlers (async)
├─ WebSocket Connections (async)
└─ Bot Thread (separate thread)
    └─ Trading Loop (synchronous)
        ├─ MT5 API calls
        ├─ Strategy calculations
        └─ WebSocket broadcasts (via asyncio.run)
```

**Key Points:**
- FastAPI runs in main thread (async)
- Bot runs in **separate daemon thread** (sync)
- Bot thread uses `asyncio.run()` to broadcast WebSocket messages
- This prevents blocking the API server

---

## 🔄 Component Interactions

### Frontend Components

**BotControl.jsx:**
- Polls `/bot/status` every 5 seconds (REST)
- Sends start/stop commands (REST)
- Displays bot status

**PriceTicker.jsx:**
- Receives `priceData` from WebSocket hook
- Updates in real-time

**AccountStats.jsx:**
- Polls `/stats/account` every 10 seconds (REST)
- Shows balance, equity, margin

**OpenPositions.jsx:**
- Polls `/stats/positions` every 5 seconds (REST)
- Shows active trades

**TradeHistory.jsx:**
- Queries `/history/trades` with pagination (REST)
- Shows past trades from database

**LogViewer.jsx:**
- Receives `logEvents` from WebSocket hook
- Shows real-time logs

---

### Backend Components

**app.py:**
- Handles HTTP requests
- Manages WebSocket connections
- Routes to bot_manager

**bot_manager.py:**
- Controls bot lifecycle
- Runs trading loop in thread
- Integrates with existing bot logic

**websocket_manager.py:**
- Manages WebSocket connections
- Broadcasts messages to all clients

**database.py:**
- Stores trade history
- Stores bot state
- Async SQLite operations

---

## 🎯 Key Design Decisions

### 1. **Non-Blocking Bot Execution**
- Bot runs in separate thread
- API remains responsive
- Can handle multiple WebSocket clients

### 2. **Existing Logic Preserved**
- Bot manager **wraps** existing code
- No modifications to strategies, risk manager, or trade logger
- Original `main.py` still works

### 3. **Real-Time Updates**
- WebSocket for live data
- REST for commands and queries
- Hybrid approach for best UX

### 4. **Separation of Concerns**
- Frontend: UI and user interaction
- Backend: API and bot control
- Bot Logic: Trading strategies and execution
- MT5: Market data and order execution

### 5. **Scalability**
- Multiple WebSocket clients supported
- Database for persistent storage
- Async operations for performance

---

## 🔐 Security Considerations

1. **CORS:** Limited to localhost:3000 and localhost:5173
2. **No Authentication:** Local-only deployment
3. **WebSocket:** No authentication (local network only)
4. **Database:** SQLite file-based (local access only)

**⚠️ WARNING:** Do NOT expose to internet without adding authentication!

---

## 📈 Performance Characteristics

- **API Response Time:** < 100ms (local)
- **WebSocket Latency:** < 50ms (local)
- **Trading Interval:** Configurable (default 60s)
- **Database Queries:** Async, non-blocking
- **Memory Usage:** ~100-200MB (depends on history)

---

## 🎓 Summary

The TraderBot system uses a **client-server architecture** with:

1. **React Frontend** - User interface with real-time updates
2. **FastAPI Backend** - REST API + WebSocket server
3. **Bot Thread** - Separate thread for trading logic
4. **WebSocket Broadcasting** - Real-time updates to all clients
5. **SQLite Database** - Persistent trade history
6. **MT5 Integration** - Trading platform connection

The key innovation is the **non-invasive wrapper** around existing bot logic, allowing the original code to remain unchanged while adding a modern web interface.

