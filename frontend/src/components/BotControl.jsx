/**
 * Bot Control Panel Component
 */

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { botAPI } from '../api/client';

const BotControl = ({ wsStatus }) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState(null);

  // Query bot status
  const { data: status, isLoading } = useQuery('botStatus', botAPI.getStatus, {
    refetchInterval: 5000,
  });

  // Start bot mutation
  const startMutation = useMutation(botAPI.start, {
    onSuccess: () => {
      queryClient.invalidateQueries('botStatus');
      setError(null);
    },
    onError: (err) => {
      setError(err.response?.data?.detail || 'Failed to start bot');
    },
  });

  // Stop bot mutation
  const stopMutation = useMutation(botAPI.stop, {
    onSuccess: () => {
      queryClient.invalidateQueries('botStatus');
      setError(null);
    },
    onError: (err) => {
      setError(err.response?.data?.detail || 'Failed to stop bot');
    },
  });

  const handleStart = () => {
    setError(null);
    startMutation.mutate({});
  };

  const handleStop = () => {
    setError(null);
    stopMutation.mutate();
  };

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-20 bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  const isRunning = status?.is_running || false;
  const canTrade = status?.can_trade ?? true;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Bot Control</h2>
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          ></div>
          <span className="text-sm font-medium text-slate-300">
            {isRunning ? 'Running' : 'Stopped'}
          </span>
        </div>
      </div>

      {/* WebSocket Status */}
      <div className="mb-4 flex items-center gap-2 text-sm">
        <div
          className={`w-2 h-2 rounded-full ${
            wsStatus ? 'bg-green-500' : 'bg-yellow-500'
          }`}
        ></div>
        <span className="text-slate-400">
          WebSocket: {wsStatus ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Status Info */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Uptime</div>
          <div className="text-white text-lg font-semibold">
            {formatUptime(status?.uptime_seconds)}
          </div>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Total Trades</div>
          <div className="text-white text-lg font-semibold">
            {status?.total_trades || 0}
          </div>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Total Profit</div>
          <div
            className={`text-lg font-semibold ${
              (status?.total_profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            ${(status?.total_profit || 0).toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Open Positions</div>
          <div className="text-white text-lg font-semibold">
            {status?.current_positions || 0}
          </div>
        </div>
      </div>

      {/* Daily P&L */}
      <div className="mb-6 p-4 bg-slate-900/50 rounded-lg">
        <div className="text-slate-400 text-sm mb-1">Daily P&L</div>
        <div
          className={`text-2xl font-bold ${
            (status?.daily_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
          }`}
        >
          ${(status?.daily_pnl || 0).toFixed(2)}
        </div>
        {!canTrade && (
          <div className="mt-2 text-yellow-400 text-sm">
            ⚠️ {status?.trade_status_reason}
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleStart}
          disabled={isRunning || startMutation.isLoading}
          className="btn-success flex-1"
        >
          {startMutation.isLoading ? 'Starting...' : 'Start Bot'}
        </button>
        <button
          onClick={handleStop}
          disabled={!isRunning || stopMutation.isLoading}
          className="btn-danger flex-1"
        >
          {stopMutation.isLoading ? 'Stopping...' : 'Stop Bot'}
        </button>
      </div>
    </div>
  );
};

export default BotControl;

