import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
import pickle
import os

logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = None
    
    def load_data(self, filepath):
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
    
    def handle_missing_values(self, df):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        logger.info("Handled missing values")
        return df
    
    def remove_outliers(self, df, columns, threshold=3):
        initial_len = len(df)
        for col in columns:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-8))
                df = df[z_scores < threshold]
        removed = initial_len - len(df)
        logger.info(f"Removed {removed} outliers")
        return df
    
    def create_features(self, df):
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["hour"] = df["timestamp"].dt.hour.fillna(12).astype(int)
            df["month"] = df["timestamp"].dt.month.fillna(6).astype(int)
        else:
            df["hour"] = 12
            df["month"] = 6
        
        logger.info("Created features")
        return df
    
    def create_target_labels(self, df):
        def determine_alert_level(row):
            wind_speed = row.get("wind_speed", 0)
            humidity = row.get("humidity", 0)
            pressure = row.get("pressure", 1013)
            temperature = row.get("temperature", 25)
            score = 0
            if wind_speed > 20:
                score += 3
            elif wind_speed > 15:
                score += 2
            elif wind_speed > 10:
                score += 1

            if humidity > 90:
                score += 2
            elif humidity > 85:
                score += 1

            if pressure < 990:
                score += 2
            elif pressure < 1005:
                score += 1

            if temperature > 35 or temperature < 5:
                score += 1

            if score >= 5:
                return 3
            elif score >= 3:
                return 2
            elif score >= 1:
                return 1
            else:
                return 0
        
        df["alert_level_numeric"] = df.apply(determine_alert_level, axis=1)
        logger.info("Created target labels")
        return df
    
    def select_features(self, df):
        feature_cols = ["temperature", "humidity", "wind_speed", "pressure", "hour", "month"]
        available_features = [f for f in feature_cols if f in df.columns]
        self.feature_names = available_features
        return df[available_features + ["alert_level_numeric"]]
    
    def normalize_features(self, X_train, X_test=None):
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
        else:
            X_test_scaled = None
        logger.info("Features normalized")
        return X_train_scaled, X_test_scaled
    
    def prepare_data(self, filepath, test_split=0.2):
        df = self.load_data(filepath)
        if df is None:
            return None
        
        df = self.handle_missing_values(df)
        df = self.remove_outliers(df, ["temperature", "humidity", "wind_speed"])
        df = self.create_features(df)
        df = self.create_target_labels(df)
        df_selected = self.select_features(df)
        
        X = df_selected.drop("alert_level_numeric", axis=1).values
        y = df_selected["alert_level_numeric"].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_split, random_state=42, stratify=y
        )
        
        X_train_scaled, X_test_scaled = self.normalize_features(X_train, X_test)
        
        logger.info("Data preparation complete")
        logger.info(f"Training set: {X_train_scaled.shape}")
        logger.info(f"Test set: {X_test_scaled.shape}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, self.scaler, self.feature_names
    
    def save_scaler(self, filepath):
        try:
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, "wb") as f:
                pickle.dump(self.scaler, f)
            logger.info("Scaler saved")
        except Exception as e:
            logger.error(f"Error saving scaler: {e}")
