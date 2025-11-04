/**
 * Price Ticker Component - Displays live price updates
 */

import React from 'react';
import { format } from 'date-fns';

const PriceTicker = ({ priceData }) => {
  if (!priceData) {
    return (
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Live Price</h2>
        <div className="text-slate-400 text-center py-8">
          Waiting for price data...
        </div>
      </div>
    );
  }

  const spread = (priceData.ask - priceData.bid).toFixed(5);
  const spreadPips = (spread * 10000).toFixed(1);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Live Price</h2>
        <span className="badge badge-info">{priceData.symbol}</span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-green-900/30 border border-green-700 p-4 rounded-lg">
          <div className="text-green-400 text-sm mb-1">BID</div>
          <div className="text-white text-2xl font-bold">
            {priceData.bid.toFixed(5)}
          </div>
        </div>
        <div className="bg-red-900/30 border border-red-700 p-4 rounded-lg">
          <div className="text-red-400 text-sm mb-1">ASK</div>
          <div className="text-white text-2xl font-bold">
            {priceData.ask.toFixed(5)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-slate-900/50 p-3 rounded">
          <div className="text-slate-400 mb-1">Last</div>
          <div className="text-white font-semibold">
            {priceData.last.toFixed(5)}
          </div>
        </div>
        <div className="bg-slate-900/50 p-3 rounded">
          <div className="text-slate-400 mb-1">Spread</div>
          <div className="text-white font-semibold">{spreadPips} pips</div>
        </div>
        <div className="bg-slate-900/50 p-3 rounded">
          <div className="text-slate-400 mb-1">Volume</div>
          <div className="text-white font-semibold">{priceData.volume}</div>
        </div>
      </div>

      <div className="mt-4 text-xs text-slate-500 text-center">
        Updated: {format(new Date(priceData.time), 'HH:mm:ss')}
      </div>
    </div>
  );
};

export default PriceTicker;

