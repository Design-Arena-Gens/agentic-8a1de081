from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "15m"

class TradingAnalyzer:
    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe

    def fetch_data(self):
        """Fetch data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(self.symbol)

            if self.timeframe == "15m":
                # Get 7 days of 15-minute data
                df = ticker.history(period="7d", interval="15m")
            else:  # 1d
                # Get 1 year of daily data
                df = ticker.history(period="1y", interval="1d")

            if df.empty:
                raise ValueError(f"No data found for {self.symbol}")

            return df
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching data: {str(e)}")

    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # Simple Moving Averages
        sma_20 = SMAIndicator(close=df['Close'], window=20)
        df['SMA_20'] = sma_20.sma_indicator()

        sma_50 = SMAIndicator(close=df['Close'], window=50)
        df['SMA_50'] = sma_50.sma_indicator()

        # RSI
        rsi = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi.rsi()

        # MACD
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()

        return df

    def generate_signal(self, df):
        """Generate trading signal based on technical indicators"""
        latest = df.iloc[-1]

        signals = []

        # Trend Analysis (SMA)
        if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
            if latest['SMA_20'] > latest['SMA_50']:
                signals.append('bullish_trend')
            else:
                signals.append('bearish_trend')

        # RSI Analysis
        if pd.notna(latest['RSI']):
            if latest['RSI'] < 30:
                signals.append('oversold')
            elif latest['RSI'] > 70:
                signals.append('overbought')

        # MACD Analysis
        if pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal']):
            if latest['MACD'] > latest['MACD_Signal']:
                signals.append('macd_bullish')
            else:
                signals.append('macd_bearish')

        # Price vs SMA
        if pd.notna(latest['SMA_20']):
            if latest['Close'] > latest['SMA_20']:
                signals.append('price_above_sma20')
            else:
                signals.append('price_below_sma20')

        # Generate final signal
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

        return signal, strength, signals

    def generate_recommendation(self, signal, strength, signals, latest):
        """Generate trading recommendation"""
        recommendations = []

        if signal == "BUY":
            recommendations.append(f"Strong buying opportunity detected for {self.symbol}.")
            if 'oversold' in signals:
                recommendations.append(f"RSI indicates oversold conditions ({latest['RSI']:.2f}).")
            if 'bullish_trend' in signals:
                recommendations.append("Short-term trend is above long-term trend (bullish).")
            if 'macd_bullish' in signals:
                recommendations.append("MACD crossed above signal line (bullish momentum).")
        elif signal == "SELL":
            recommendations.append(f"Consider selling or taking profits on {self.symbol}.")
            if 'overbought' in signals:
                recommendations.append(f"RSI indicates overbought conditions ({latest['RSI']:.2f}).")
            if 'bearish_trend' in signals:
                recommendations.append("Short-term trend is below long-term trend (bearish).")
            if 'macd_bearish' in signals:
                recommendations.append("MACD crossed below signal line (bearish momentum).")
        else:
            recommendations.append(f"Hold position and wait for clearer signals on {self.symbol}.")
            recommendations.append("Market conditions are neutral or mixed.")

        return " ".join(recommendations)

    def analyze(self):
        """Perform complete analysis"""
        df = self.fetch_data()
        df = self.calculate_indicators(df)

        signal, strength, signals = self.generate_signal(df)
        latest = df.iloc[-1]

        recommendation = self.generate_recommendation(signal, strength, signals, latest)

        # Prepare price data for chart (last 50 points)
        chart_data = df.tail(50).reset_index()
        price_data = []
        for _, row in chart_data.iterrows():
            price_data.append({
                'timestamp': row['Datetime'].strftime('%Y-%m-%d %H:%M') if self.timeframe == '15m' else row['Date'].strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
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

@app.get("/")
def read_root():
    return {"message": "Trading Data Platform API", "status": "active"}

@app.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    """Analyze stock and generate trading signals"""
    try:
        analyzer = TradingAnalyzer(request.symbol, request.timeframe)
        result = analyzer.analyze()
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
