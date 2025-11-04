/**
 * Trade History Component
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { historyAPI } from '../api/client';
import { format } from 'date-fns';

const TradeHistory = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery(
    ['tradeHistory', page, statusFilter],
    () =>
      historyAPI.getTrades({
        page,
        page_size: 20,
        status: statusFilter || undefined,
      }),
    {
      keepPreviousData: true,
    }
  );

  const getStatusBadge = (status) => {
    const badges = {
      OPEN: 'badge-info',
      CLOSED: 'badge-success',
      FAILED: 'badge-danger',
    };
    return badges[status] || 'badge-info';
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Trade History</h2>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-700 text-white px-3 py-1 rounded text-sm border border-slate-600"
        >
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="CLOSED">Closed</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-slate-700 rounded animate-pulse"></div>
          ))}
        </div>
      ) : data?.trades.length === 0 ? (
        <div className="text-slate-400 text-center py-8">No trades found</div>
      ) : (
        <>
          <div className="space-y-2 mb-4 max-h-96 overflow-y-auto">
            {data?.trades.map((trade) => (
              <div
                key={trade.id}
                className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`badge ${
                        trade.action === 'BUY' ? 'badge-success' : 'badge-danger'
                      }`}
                    >
                      {trade.action}
                    </span>
                    <span className="text-white font-semibold">{trade.symbol}</span>
                    <span className={`badge ${getStatusBadge(trade.status)}`}>
                      {trade.status}
                    </span>
                  </div>
                  <div className="text-slate-400 text-xs">
                    {format(new Date(trade.timestamp), 'MMM dd, HH:mm:ss')}
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <div className="text-slate-400 text-xs">Entry</div>
                    <div className="text-white font-medium">
                      {trade.entry_price.toFixed(5)}
                    </div>
                  </div>
                  {trade.exit_price && (
                    <div>
                      <div className="text-slate-400 text-xs">Exit</div>
                      <div className="text-white font-medium">
                        {trade.exit_price.toFixed(5)}
                      </div>
                    </div>
                  )}
                  <div>
                    <div className="text-slate-400 text-xs">Volume</div>
                    <div className="text-white font-medium">{trade.volume}</div>
                  </div>
                  {trade.profit !== null && (
                    <div>
                      <div className="text-slate-400 text-xs">Profit</div>
                      <div
                        className={`font-medium ${
                          trade.profit >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        ${trade.profit.toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>

                {trade.strategy && (
                  <div className="mt-2 text-xs text-slate-500">
                    Strategy: {trade.strategy}
                    {trade.risk_reward_ratio && (
                      <span className="ml-2">R/R: {trade.risk_reward_ratio.toFixed(2)}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-700">
              <div className="text-sm text-slate-400">
                Page {data.page} of {data.total_pages} ({data.total} total)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                  className="btn-secondary text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TradeHistory;

