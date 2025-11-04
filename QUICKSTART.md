# TraderBot Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.12+ installed
- [ ] Node.js 18+ installed
- [ ] MetaTrader 5 installed and logged in
- [ ] Trading account (demo or live)

## Setup (One-Time)

```bash
# Run automated setup
setup-all.bat
```

This will:
1. Create Python virtual environment
2. Install all Python dependencies
3. Install all Node.js dependencies

**Estimated time**: 2-3 minutes

## Running the Application

### Option 1: Web Dashboard (Recommended)

**Terminal 1 - Backend:**
```bash
start-backend.bat
```
✅ Backend running at http://localhost:5000

**Terminal 2 - Frontend:**
```bash
start-frontend.bat
```
✅ Dashboard at http://localhost:3000

### Option 2: Standalone Bot

```bash
python main.py
```

## Using the Dashboard

1. **Open Dashboard**: http://localhost:3000

2. **Start Trading**:
   - Click "Start Bot" button
   - Bot status changes to "Running"
   - Watch live price updates

3. **Monitor**:
   - View open positions
   - Check trade history
   - Monitor logs
   - Track account stats

4. **Stop Trading**:
   - Click "Stop Bot" button
   - Bot stops gracefully

## API Documentation

Visit http://localhost:5000/docs for interactive API documentation.

## Troubleshooting

### Backend won't start
- Check if Python virtual environment is activated
- Verify MT5 is running and logged in
- Check port 5000 is not in use

### Frontend won't start
- Check if Node.js is installed
- Verify node_modules exists (run `npm install` in frontend/)
- Check port 3000 is not in use

### WebSocket not connecting
- Ensure backend is running on port 5000
- Check firewall settings
- Refresh browser page

### Bot won't start
- Verify MT5 is logged in
- Check symbol is available in Market Watch
- Review logs for error messages

## Configuration

Edit `config/settings.json` to customize:
- Trading symbol
- Volume (lot size)
- Trade interval
- Risk management
- Strategy settings

## Support

- **Full Setup Guide**: See SETUP.md
- **Integration Details**: See INTEGRATION_SUMMARY.md
- **User Guide**: See README.md
- **API Docs**: http://localhost:5000/docs

## Safety Reminders

⚠️ **Always test on demo account first**
⚠️ **Set appropriate daily loss limits**
⚠️ **Monitor the bot regularly**
⚠️ **Never expose API to internet without authentication**

---

**Ready to trade?** Start the backend and frontend, then click "Start Bot" in the dashboard!

