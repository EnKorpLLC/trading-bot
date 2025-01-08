import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
import joblib
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.model_manager import ModelManager

class PredictiveAnalytics:
    def __init__(self):
        self.model_manager = ModelManager()
        self.scaler = StandardScaler()
        
    def calculate_technical_features(self, df):
        """Calculate technical indicators for feature engineering"""
        features = pd.DataFrame(index=df.index)
        
        # Moving averages
        features['sma_20'] = df['close'].rolling(window=20).mean()
        features['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Relative Strength Index (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = exp1 - exp2
        features['signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        
        # Volatility (ATR)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        features['atr'] = true_range.rolling(14).mean()
        
        return features.fillna(0)
    
    def prepare_features(self, df):
        """Prepare features for prediction"""
        features = self.calculate_technical_features(df)
        return self.scaler.fit_transform(features)
    
    def generate_labels(self, df, threshold=0.001):
        """Generate labels for training"""
        returns = df['close'].pct_change()
        labels = np.zeros(len(returns))
        labels[returns > threshold] = 1  # Upward trend
        labels[returns < -threshold] = -1  # Downward trend
        return labels[1:]  # Remove first row since we can't calculate return for it
    
    def train_models(self, df):
        """Train both pattern recognition and price prediction models"""
        features = self.prepare_features(df)
        labels = self.generate_labels(df)
        
        # Train pattern recognition model
        self.model_manager.train_pattern_recognition(features[:-1], labels)
        
        # Train price prediction model
        self.model_manager.train_price_prediction(features[:-1], df['close'].values[1:])
        
    def predict_market_conditions(self, df):
        """Predict market conditions using both models"""
        features = self.prepare_features(df)
        
        # Get predictions from both models
        pattern = self.model_manager.predict_pattern(features[-1:])
        price = self.model_manager.predict_price(features[-1:])
        
        return {
            'market_pattern': int(pattern[0]),
            'predicted_price': float(price[0]),
            'current_price': float(df['close'].iloc[-1]),
            'timestamp': str(df.index[-1])
        } 