import logging
import psycopg2
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from config import DB_CONFIG, ML_CONFIG

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.conn = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to database")
            return True
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
    
    def generate_synthetic_data(self, days=90, records_per_day=8):
        """Generate realistic synthetic coastal weather data"""
        logger.info(f"Generating {days * records_per_day} synthetic weather records for {days} days...")
        
        np.random.seed(42)
        records = []
        start_date = datetime.now() - timedelta(days=days)
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            month = current_date.month
            base_temp = 20 + 10 * np.sin(2 * np.pi * month / 12)
            
            for hour in range(0, 24, 3):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                
                hour_factor = np.sin(2 * np.pi * hour / 24)
                temperature = base_temp + 8 * hour_factor + np.random.normal(0, 2)
                temperature = np.clip(temperature, -5, 45)
                
                humidity = 70 - 10 * hour_factor + np.random.normal(0, 5)
                humidity = np.clip(humidity, 30, 100)
                
                # Periodically inject severe weather/storm events for balanced dataset
                rand_val = np.random.random()
                if rand_val < 0.05: # Severe storm / cyclone
                    wind_speed = np.random.uniform(22, 35)
                    humidity = np.random.uniform(91, 100)
                    pressure = np.random.uniform(970, 995)
                elif rand_val < 0.15: # High wind / heavy weather
                    wind_speed = np.random.uniform(16, 24)
                    humidity = np.random.uniform(86, 95)
                    pressure = np.random.uniform(995, 1008)
                else:
                    base_wind = 5 + 3 * np.sin(2 * np.pi * month / 12)
                    wind_speed = base_wind + np.random.exponential(2)
                    wind_speed = np.clip(wind_speed, 0, 35)
                    pressure = 1010 - 5 * np.sin(2 * np.pi * month / 12) + np.random.normal(0, 3)
                    pressure = np.clip(pressure, 980, 1020)
                
                alert_level = self._determine_alert_level(temperature, humidity, wind_speed, pressure)
                
                records.append({
                    "timestamp": timestamp,
                    "temperature": round(temperature, 2),
                    "humidity": round(humidity, 2),
                    "wind_speed": round(wind_speed, 2),
                    "pressure": round(pressure, 2),
                    "alert_level": alert_level
                })
        
        df = pd.DataFrame(records)
        counts = df["alert_level"].value_counts()
        stats = ", ".join([f"{level}: {counts.get(level, 0)}" for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]])
        logger.info(f"✓ Generated {len(df)} records - Alert distribution: {stats}")
        return df
    
    def _determine_alert_level(self, temperature, humidity, wind_speed, pressure):
        """Determine alert level based on coastal threat parameters"""
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
        if temperature > 35 or temperature < 5:
            score += 1
        if pressure < 990:
            score += 2
        
        if score >= 5:
            return "CRITICAL"
        elif score >= 3:
            return "HIGH"
        elif score >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def collect_weather_data(self, days=90):
        """Collect historical weather data from database, fallback to synthetic"""
        if self.connect():
            try:
                cursor = self.conn.cursor()
                query = """
                    SELECT w.timestamp, w.temperature, w.humidity, w.wind_speed, w.pressure,
                           COALESCE(a.severity, 'LOW') AS alert_level
                    FROM weather_data w
                    LEFT JOIN alerts a ON w.timestamp = a.observed_at
                    WHERE w.timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY w.timestamp DESC
                """
                cursor.execute(query, (days,))
                rows = cursor.fetchall()
                cursor.close()
                self.disconnect()
                
                if rows and len(rows) > 0:
                    df = pd.DataFrame(rows, columns=["timestamp", "temperature", "humidity", "wind_speed", "pressure", "alert_level"])
                    logger.info(f"✓ Collected {len(df)} records from database")
                    return df
                else:
                    logger.warning("Database returned no data - generating synthetic data")
                    return self.generate_synthetic_data(days)
            except Exception as e:
                logger.warning(f"Database query failed - generating synthetic data")
                self.disconnect()
                return self.generate_synthetic_data(days)
        else:
            logger.info("Generating synthetic coastal weather data...")
            return self.generate_synthetic_data(days)
    
    def validate_data(self, df):
        """Validate collected data"""
        if df is None or len(df) == 0:
            logger.error("Data is empty")
            return False
        min_records = ML_CONFIG["data"]["min_historical_records"]
        if len(df) < min_records:
            logger.error(f"Insufficient data: {len(df)} < {min_records}")
            return False
        required_columns = ["temperature", "humidity", "wind_speed", "pressure", "alert_level"]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.error(f"Missing columns: {missing}")
            return False
        logger.info(f"✓ Data validation passed ({len(df)} records)")
        return True
    
    def save_data_to_csv(self, df, filename="data/training_data.csv"):
        """Save data to CSV file"""
        try:
            os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
            df.to_csv(filename, index=False)
            logger.info(f"✓ Data saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False
