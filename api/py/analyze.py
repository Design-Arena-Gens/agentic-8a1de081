from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/py/analyze':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            symbol = data.get('symbol', 'AAPL')
            timeframe = data.get('timeframe', '15m')

            try:
                result = self.analyze_stock(symbol, timeframe)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def analyze_stock(self, symbol, timeframe):
        # Fetch data
        ticker = yf.Ticker(symbol)

        if timeframe == "15m":
            df = ticker.history(period="7d", interval="15m")
        else:
            df = ticker.history(period="1y", interval="1d")

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Calculate SMA
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()

        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Calculate MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        latest = df.iloc[-1]

        # Generate signals
        signals = []
        if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
            if latest['SMA_20'] > latest['SMA_50']:
                signals.append('bullish_trend')
            else:
                signals.append('bearish_trend')

        if pd.notna(latest['RSI']):
            if latest['RSI'] < 30:
                signals.append('oversold')
            elif latest['RSI'] > 70:
                signals.append('overbought')

        if pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal']):
            if latest['MACD'] > latest['MACD_Signal']:
                signals.append('macd_bullish')
            else:
                signals.append('macd_bearish')

        if pd.notna(latest['SMA_20']):
            if latest['Close'] > latest['SMA_20']:
                signals.append('price_above_sma20')
            else:
                signals.append('price_below_sma20')

        bullish_signals = sum([
            'bullish_trend' in signals,
            'oversold' in signals,
            'macd_bullish' in signals,
            'price_above_sma20' in signals
        ])

        bearish_signals = sum([
            'bearish_trend' in signals,
            'overbought' in signals,
            'macd_bearish' in signals,
            'price_below_sma20' in signals
        ])

        if bullish_signals >= 3:
            signal = "BUY"
            strength = "STRONG"
        elif bullish_signals >= 2:
            signal = "BUY"
            strength = "MODERATE"
        elif bearish_signals >= 3:
            signal = "SELL"
            strength = "STRONG"
        elif bearish_signals >= 2:
            signal = "SELL"
            strength = "MODERATE"
        else:
            signal = "HOLD"
            strength = "NEUTRAL"

        # Generate recommendation
        recommendations = []
        if signal == "BUY":
            recommendations.append(f"Strong buying opportunity detected for {symbol}.")
            if 'oversold' in signals:
                recommendations.append(f"RSI indicates oversold conditions ({latest['RSI']:.2f}).")
        elif signal == "SELL":
            recommendations.append(f"Consider selling or taking profits on {symbol}.")
            if 'overbought' in signals:
                recommendations.append(f"RSI indicates overbought conditions ({latest['RSI']:.2f}).")
        else:
            recommendations.append(f"Hold position and wait for clearer signals on {symbol}.")

        recommendation = " ".join(recommendations)

        # Prepare chart data
        chart_data = df.tail(50).reset_index()
        price_data = []
        for _, row in chart_data.iterrows():
            ts = row.get('Datetime') or row.get('Date')
            price_data.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M') if timeframe == '15m' else ts.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'current_price': float(latest['Close']),
            'signal': signal,
            'signal_strength': strength,
            'indicators': {
                'sma_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else 0,
                'sma_50': float(latest['SMA_50']) if pd.notna(latest['SMA_50']) else 0,
                'rsi': float(latest['RSI']) if pd.notna(latest['RSI']) else 0,
                'macd': float(latest['MACD']) if pd.notna(latest['MACD']) else 0,
                'macd_signal': float(latest['MACD_Signal']) if pd.notna(latest['MACD_Signal']) else 0,
            },
            'recommendation': recommendation,
            'price_data': price_data
        }
