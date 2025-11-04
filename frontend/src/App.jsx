/**
 * Main App Component
 */

import React from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import BotControl from './components/BotControl';
import PriceTicker from './components/PriceTicker';
import AccountStats from './components/AccountStats';
import OpenPositions from './components/OpenPositions';
import TradeHistory from './components/TradeHistory';
import LogViewer from './components/LogViewer';

function App() {
  const {
    isConnected,
    priceData,
    tradeExecutions,
    logEvents,
    botStatus,
  } = useWebSocket();

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">TraderBot Dashboard</h1>
              <p className="text-slate-400 text-sm mt-1">
                MetaTrader 5 Automated Trading System
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-slate-400">WebSocket</div>
                <div
                  className={`text-sm font-semibold ${
                    isConnected ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {isConnected ? 'Connected' : 'Disconnected'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-1 space-y-6">
            <BotControl wsStatus={isConnected} />
            <PriceTicker priceData={priceData} />
            <AccountStats />
          </div>

          {/* Middle Column */}
          <div className="lg:col-span-1 space-y-6">
            <OpenPositions />
            <LogViewer logEvents={logEvents} />
          </div>

          {/* Right Column */}
          <div className="lg:col-span-1 space-y-6">
            <TradeHistory />
          </div>
        </div>

        {/* Trade Executions Banner */}
        {tradeExecutions.length > 0 && (
          <div className="fixed bottom-4 right-4 max-w-md space-y-2">
            {tradeExecutions.slice(0, 3).map((trade, index) => (
              <div
                key={index}
                className={`card ${
                  trade.success ? 'border-green-500' : 'border-red-500'
                } border-2 animate-slide-in`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`badge ${
                          trade.action === 'BUY' ? 'badge-success' : 'badge-danger'
                        }`}
                      >
                        {trade.action}
                      </span>
                      <span className="text-white font-semibold">{trade.symbol}</span>
                    </div>
                    <div className="text-sm text-slate-300">{trade.message}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{trade.price.toFixed(5)}</div>
                    <div className="text-xs text-slate-400">{trade.strategy}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 border-t border-slate-700 mt-12">
        <div className="container mx-auto px-4 py-4">
          <div className="text-center text-slate-400 text-sm">
            TraderBot v1.0.0 | MetaTrader 5 Integration
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

