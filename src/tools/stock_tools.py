from smolagents import Tool
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import ta

class StockPredictionTool(Tool):
    name = "stock_prediction"
    description = "Predict stock prices for the next 7 days using technical analysis and machine learning"
    inputs = {
        "ticker": {
            "type": "string",
            "description": "Stock ticker symbol (e.g., AAPL, GOOGL)",
            "required": True
        }
    }
    output_type = "json"

    def __init__(self):
        super().__init__()
        self.scaler = MinMaxScaler()
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

    def _get_stock_data(self, ticker: str) -> pd.DataFrame:
        """Fetch historical stock data and calculate technical indicators."""
        # Get data for the last 60 days (30 for training, 30 for features)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        # Fetch data
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        # Calculate technical indicators
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['MACD'] = ta.trend.MACD(df['Close']).macd()
        df['BB_upper'] = ta.volatility.BollingerBands(df['Close']).bollinger_hband()
        df['BB_lower'] = ta.volatility.BollingerBands(df['Close']).bollinger_lband()
        df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
        df['EMA_20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        
        # Add price changes
        df['Price_Change'] = df['Close'].pct_change()
        df['Volume_Change'] = df['Volume'].pct_change()
        
        # Drop any NaN values
        df = df.dropna()
        
        return df

    def _prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prepare features for prediction."""
        features = [
            'Close', 'Volume', 'RSI', 'MACD', 
            'BB_upper', 'BB_lower', 'SMA_20', 'EMA_20',
            'Price_Change', 'Volume_Change'
        ]
        
        X = df[features].values
        y = df['Close'].values
        
        # Scale the features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y

    def _create_sequences(self, X: np.ndarray, y: np.ndarray, lookback: int = 30) -> tuple:
        """Create sequences for training."""
        X_seq, y_seq = [], []
        
        for i in range(len(X) - lookback):
            X_seq.append(X[i:i + lookback])
            y_seq.append(y[i + lookback])
            
        return np.array(X_seq), np.array(y_seq)

    def _predict_next_days(self, model, last_sequence: np.ndarray, days: int = 7) -> List[float]:
        """Predict the next n days of stock prices."""
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(days):
            # Predict the next day
            pred = model.predict(current_sequence.reshape(1, -1))[0]
            predictions.append(pred)
            
            # Update the sequence
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = pred
            
        return predictions

    def forward(self, **inputs) -> Dict[str, Any]:
        ticker = inputs["ticker"].upper()
        
        try:
            # Get stock data and calculate indicators
            df = self._get_stock_data(ticker)
            
            # Prepare features
            X, y = self_prepare_features(df)
            
            # Create sequences
            X_seq, y_seq = self._create_sequences(X, y)
            
            # Train the model
            self.model.fit(X_seq, y_seq)
            
            # Get the last sequence for prediction
            last_sequence = X_seq[-1]
            
            # Make predictions
            predictions = self._predict_next_days(self.model, last_sequence)
            
            # Get current stock info
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('regularMarketPrice', 0)
            
            # Calculate prediction dates
            prediction_dates = [
                (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(1, 8)
            ]
            
            # Prepare technical analysis summary
            last_row = df.iloc[-1]
            analysis = {
                "RSI": "Overbought" if last_row['RSI'] > 70 else "Oversold" if last_row['RSI'] < 30 else "Neutral",
                "MACD": "Bullish" if last_row['MACD'] > 0 else "Bearish",
                "Bollinger": "Upper Band" if last_row['Close'] > last_row['BB_upper'] else 
                            "Lower Band" if last_row['Close'] < last_row['BB_lower'] else "Middle",
                "Trend": "Upward" if last_row['Close'] > last_row['SMA_20'] else "Downward"
            }
            
            return {
                "ticker": ticker,
                "current_price": current_price,
                "predictions": {
                    date: round(price, 2)
                    for date, price in zip(prediction_dates, predictions)
                },
                "technical_analysis": analysis,
                "confidence_metrics": {
                    "model_score": round(self.model.score(X_seq, y_seq), 3),
                    "last_30_days_volatility": round(df['Close'].pct_change().std() * 100, 2)
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to predict stock prices: {str(e)}",
                "ticker": ticker
            } 