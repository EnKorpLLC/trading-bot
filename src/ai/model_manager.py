import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Tuple, Union

class ModelManager:
    def __init__(self, model_path: str = "models"):
        self.model_path = model_path
        self.models: Dict[str, Union[RandomForestClassifier, GradientBoostingRegressor]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        os.makedirs(model_path, exist_ok=True)
    
    def train_pattern_recognition_model(self, features: np.ndarray, labels: np.ndarray, model_name: str = "pattern_recognition"):
        """Train a pattern recognition model using Random Forest"""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_scaled, labels)
        
        self.models[model_name] = model
        self.scalers[model_name] = scaler
        
        # Save the model and scaler
        joblib.dump(model, os.path.join(self.model_path, f"{model_name}.joblib"))
        joblib.dump(scaler, os.path.join(self.model_path, f"{model_name}_scaler.joblib"))
    
    def train_price_prediction_model(self, features: np.ndarray, targets: np.ndarray, model_name: str = "price_prediction"):
        """Train a price prediction model using Gradient Boosting"""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)
        
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, targets)
        
        self.models[model_name] = model
        self.scalers[model_name] = scaler
        
        joblib.dump(model, os.path.join(self.model_path, f"{model_name}.joblib"))
        joblib.dump(scaler, os.path.join(self.model_path, f"{model_name}_scaler.joblib"))
    
    def predict(self, features: np.ndarray, model_name: str) -> np.ndarray:
        """Make predictions using the specified model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
            
        X_scaled = self.scalers[model_name].transform(features)
        return self.models[model_name].predict(X_scaled)
    
    def load_model(self, model_name: str) -> Tuple[Any, StandardScaler]:
        """Load a saved model and its scaler"""
        model = joblib.load(os.path.join(self.model_path, f"{model_name}.joblib"))
        scaler = joblib.load(os.path.join(self.model_path, f"{model_name}_scaler.joblib"))
        
        self.models[model_name] = model
        self.scalers[model_name] = scaler
        return model, scaler 