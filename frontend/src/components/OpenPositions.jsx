/**
 * Open Positions Component
 */

import React from 'react';
import { useQuery } from 'react-query';
import { statsAPI } from '../api/client';
import { format } from 'date-fns';

const OpenPositions = () => {
  const { data: positions, isLoading } = useQuery(
    'openPositions',
    statsAPI.getPositions,
    {
      refetchInterval: 5000,
    }
  );

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Open Positions</h2>
        <span className="badge badge-info">{positions?.length || 0}</span>
      </div>

      {!positions || positions.length === 0 ? (
        <div className="text-slate-400 text-center py-8">No open positions</div>
      ) : (
        <div className="space-y-3">
          {positions.map((position) => (
            <div
              key={position.ticket}
              className="bg-slate-900/50 p-4 rounded-lg border border-slate-700"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`badge ${
                      position.type === 'BUY' ? 'badge-success' : 'badge-danger'
                    }`}
                  >
                    {position.type}
                  </span>
                  <span className="text-white font-semibold">{position.symbol}</span>
                  <span className="text-slate-400 text-sm">#{position.ticket}</span>
                </div>
                <div
                  className={`text-lg font-bold ${
                    position.profit >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  ${position.profit.toFixed(2)}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-sm mb-2">
                <div>
                  <div className="text-slate-400 text-xs">Open Price</div>
                  <div className="text-white font-medium">
                    {position.price_open.toFixed(5)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-xs">Current Price</div>
                  <div className="text-white font-medium">
                    {position.price_current.toFixed(5)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-xs">Volume</div>
                  <div className="text-white font-medium">{position.volume}</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <div className="text-slate-400 text-xs">SL</div>
                  <div className="text-white font-medium">
                    {position.sl > 0 ? position.sl.toFixed(5) : 'None'}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-xs">TP</div>
                  <div className="text-white font-medium">
                    {position.tp > 0 ? position.tp.toFixed(5) : 'None'}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-xs">Opened</div>
                  <div className="text-white font-medium">
                    {format(new Date(position.time), 'HH:mm:ss')}
                  </div>
                </div>
              </div>

              {position.comment && (
                <div className="mt-2 text-xs text-slate-500">{position.comment}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OpenPositions;

