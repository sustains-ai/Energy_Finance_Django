"""
Machine Learning models for energy project predictions.
"""

import os
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from pandas import DataFrame
import joblib


class PowerGenerationPredictor:
    """Machine learning model to predict power generation based on weather and system parameters"""
    
    def __init__(self):
        """Initialize the model"""
        self.model = None
        self.model_path = os.path.join(os.path.dirname(__file__), 'data', 'power_generation_model.joblib')
        
        # Try to load a pre-trained model if it exists
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
        except Exception as e:
            print(f"Could not load model from {self.model_path}: {e}")
            
        # If no model is loaded, create a new one
        if self.model is None:
            self._create_model()
            
    def _create_model(self):
        """Create a new model pipeline"""
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ))
        ])
    
    def train(self, X, y):
        """Train the model with the given data"""
        # Ensure model exists
        if self.model is None:
            self._create_model()
            
        # Train the model
        self.model.fit(X, y)
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        
    def predict(self, features):
        """Make a prediction with the model"""
        # Ensure model exists
        if self.model is None:
            X, y = self.generate_sample_data()
            self.train(X, y)
            
        # Make prediction
        return self.model.predict(features)
        
    def generate_sample_data(self, n_samples=1000):
        """Generate sample data for demonstration purposes"""
        # Generate random input features
        np.random.seed(42)  # for reproducibility
        
        # Create features
        data = {
            # Weather variables
            'solar_irradiance': np.random.uniform(0, 1200, n_samples),  # W/m^2
            'temperature': np.random.uniform(-10, 45, n_samples),  # Celsius
            'cloud_cover': np.random.uniform(0, 100, n_samples),  # percentage
            
            # System variables
            'system_capacity': np.random.uniform(1, 100, n_samples),  # kW
            'tilt_angle': np.random.uniform(0, 45, n_samples),  # degrees
            'azimuth': np.random.uniform(90, 270, n_samples),  # degrees (90=east, 180=south, 270=west)
            'panel_efficiency': np.random.uniform(15, 25, n_samples),  # percentage
            
            # Time variables
            'hour_of_day': np.random.randint(0, 24, n_samples),  # 0-23
            'month': np.random.randint(1, 13, n_samples)  # 1-12
        }
        
        X = DataFrame(data)
        
        # Generate target variable (realistic power output model)
        # Base power: capacity * irradiance * panel efficiency
        base_power = (X['system_capacity'] * X['solar_irradiance'] * X['panel_efficiency'] / 100) / 1000  # in kW
        
        # Hour of day effect (bell curve peaking at noon)
        hour_factor = -((X['hour_of_day'] - 12) ** 2) / 40 + 1
        hour_factor = np.maximum(0, hour_factor)
        
        # Month effect (seasonal variation)
        month_factor = np.sin((X['month'] - 1) * np.pi / 6) * 0.3 + 0.7
        
        # Temperature effect (efficiency drops when too hot or too cold)
        temp_factor = -((X['temperature'] - 25) ** 2) / 500 + 1
        temp_factor = np.maximum(0.8, temp_factor)
        
        # Cloud cover effect (reduces output)
        cloud_factor = 1 - (X['cloud_cover'] / 100) * 0.8
        
        # Tilt and azimuth effect (optimal is tilt=latitude, azimuth=180 in northern hemisphere)
        tilt_factor = -((X['tilt_angle'] - 30) ** 2) / 800 + 1
        azimuth_factor = -((X['azimuth'] - 180) ** 2) / 5000 + 1
        orientation_factor = np.maximum(0.85, tilt_factor * azimuth_factor)
        
        # Combine all factors
        y = base_power * hour_factor * month_factor * temp_factor * cloud_factor * orientation_factor
        
        # Add some noise
        noise = np.random.normal(0, 0.05, n_samples) * y
        y = y + noise
        
        # Make sure power is non-negative
        y = np.maximum(0, y)
        
        # Train the model with this data
        if self.model is None:
            self._create_model()
        self.train(X, y)
        
        return X, y
        
    def evaluate_model(self, X, y):
        """Evaluate the model performance"""
        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train the model
        self.train(X_train, y_train)
        
        # Make predictions
        y_pred = self.predict(X_test)
        
        # Calculate metrics
        mse = np.mean((y_test - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_test - y_pred))
        
        # Calculate R-squared
        y_mean = np.mean(y_test)
        ss_total = np.sum((y_test - y_mean) ** 2)
        ss_residual = np.sum((y_test - y_pred) ** 2)
        r_squared = 1 - (ss_residual / ss_total)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r_squared': r_squared
        }