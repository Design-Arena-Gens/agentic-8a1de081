'use client';

import { useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PriceData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface AnalysisResult {
  symbol: string;
  timeframe: string;
  current_price: number;
  signal: string;
  signal_strength: string;
  indicators: {
    sma_20: number;
    sma_50: number;
    rsi: number;
    macd: number;
    macd_signal: number;
  };
  recommendation: string;
  price_data: PriceData[];
}

export default function Home() {
  const [symbol, setSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState('15m');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');

  const analyzeStock = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('/api/analyze', {
        symbol,
        timeframe
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to analyze stock');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'BUY') return 'text-green-600';
    if (signal === 'SELL') return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSignalBgColor = (signal: string) => {
    if (signal === 'BUY') return 'bg-green-100 border-green-600';
    if (signal === 'SELL') return 'bg-red-100 border-red-600';
    return 'bg-yellow-100 border-yellow-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Trading Data Platform</h1>
          <p className="text-gray-600 mb-8">Yahoo Finance Technical Analysis</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stock Symbol
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="AAPL"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="15m">15 Minutes</option>
                <option value="1d">Daily</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={analyzeStock}
                disabled={loading || !symbol}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}
        </div>

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-800">{result.symbol}</h2>
                  <p className="text-gray-600">Timeframe: {result.timeframe}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-800">${result.current_price.toFixed(2)}</p>
                  <p className="text-sm text-gray-600">Current Price</p>
                </div>
              </div>

              <div className={`border-2 rounded-lg p-6 mb-6 ${getSignalBgColor(result.signal)}`}>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-gray-700 mb-1">Trading Signal</p>
                    <p className={`text-4xl font-bold ${getSignalColor(result.signal)}`}>
                      {result.signal}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-700 mb-1">Strength</p>
                    <p className="text-2xl font-bold text-gray-800">{result.signal_strength}</p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="text-sm font-semibold text-gray-700 mb-1">Recommendation:</p>
                <p className="text-gray-800">{result.recommendation}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">SMA 20</p>
                  <p className="text-lg font-bold text-gray-800">${result.indicators.sma_20.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">SMA 50</p>
                  <p className="text-lg font-bold text-gray-800">${result.indicators.sma_50.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">RSI</p>
                  <p className="text-lg font-bold text-gray-800">{result.indicators.rsi.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">MACD</p>
                  <p className="text-lg font-bold text-gray-800">{result.indicators.macd.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">MACD Signal</p>
                  <p className="text-lg font-bold text-gray-800">{result.indicators.macd_signal.toFixed(2)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Price Chart</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={result.price_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis domain={['auto', 'auto']} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={2} name="Close Price" />
                  <Line type="monotone" dataKey="high" stroke="#10b981" strokeWidth={1} name="High" />
                  <Line type="monotone" dataKey="low" stroke="#ef4444" strokeWidth={1} name="Low" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
