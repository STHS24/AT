/**
 * Log Viewer Component - Displays real-time log events
 */

import React from 'react';
import { format } from 'date-fns';

const LogViewer = ({ logEvents }) => {
  const getLevelColor = (level) => {
    const colors = {
      INFO: 'text-blue-400',
      WARNING: 'text-yellow-400',
      ERROR: 'text-red-400',
    };
    return colors[level] || 'text-slate-400';
  };

  const getLevelBadge = (level) => {
    const badges = {
      INFO: 'badge-info',
      WARNING: 'badge-warning',
      ERROR: 'badge-danger',
    };
    return badges[level] || 'badge-info';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-white mb-4">Live Logs</h2>

      {logEvents.length === 0 ? (
        <div className="text-slate-400 text-center py-8">No log events yet</div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {logEvents.map((log, index) => (
            <div
              key={index}
              className="bg-slate-900/50 p-3 rounded border border-slate-700 text-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className={`badge ${getLevelBadge(log.level)}`}>{log.level}</span>
                <span className="text-slate-500 text-xs">
                  {format(new Date(log.timestamp), 'HH:mm:ss')}
                </span>
              </div>
              <div className={`${getLevelColor(log.level)} font-mono text-xs`}>
                {log.message}
              </div>
              {log.source && (
                <div className="text-slate-500 text-xs mt-1">Source: {log.source}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LogViewer;

