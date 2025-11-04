/**
 * Account Statistics Component
 */

import React from 'react';
import { useQuery } from 'react-query';
import { statsAPI } from '../api/client';

const AccountStats = () => {
  const { data: account, isLoading, error } = useQuery(
    'accountStats',
    statsAPI.getAccount,
    {
      refetchInterval: 10000,
      retry: 1,
    }
  );

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Account Statistics</h2>
        <div className="text-red-400 text-sm">
          Failed to load account data. Make sure MT5 is running.
        </div>
      </div>
    );
  }

  const marginLevel = account?.margin_level || 0;
  const marginLevelColor =
    marginLevel > 200 ? 'text-green-400' : marginLevel > 100 ? 'text-yellow-400' : 'text-red-400';

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-white mb-4">Account Statistics</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Balance</div>
          <div className="text-white text-xl font-bold">
            {account?.currency} {account?.balance.toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Equity</div>
          <div className="text-white text-xl font-bold">
            {account?.currency} {account?.equity.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Profit</div>
          <div
            className={`text-xl font-bold ${
              (account?.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {account?.currency} {account?.profit.toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <div className="text-slate-400 text-sm mb-1">Free Margin</div>
          <div className="text-white text-xl font-bold">
            {account?.currency} {account?.free_margin.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="bg-slate-900/50 p-4 rounded-lg mb-4">
        <div className="text-slate-400 text-sm mb-1">Margin Level</div>
        <div className={`text-2xl font-bold ${marginLevelColor}`}>
          {marginLevel.toFixed(2)}%
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-slate-900/50 p-3 rounded">
          <div className="text-slate-400 mb-1">Leverage</div>
          <div className="text-white font-semibold">1:{account?.leverage}</div>
        </div>
        <div className="bg-slate-900/50 p-3 rounded">
          <div className="text-slate-400 mb-1">Server</div>
          <div className="text-white font-semibold truncate">{account?.server}</div>
        </div>
      </div>
    </div>
  );
};

export default AccountStats;

