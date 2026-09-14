import os, logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create data_collector.py
with open('ml_models/data_collector.py', 'w') as f:
    f.write('''import psycopg2
from config import DB_CONFIG, ML_CONFIG
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.conn = None
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
    
    def collect_weather_data(self, days=90):
        if not self.connect():
            return None
        
        try:
            cursor = self.conn.cursor()
            query = """SELECT w.city, w.temperature, w.humidity, w.wind_speed, w.pressure,
                   w.description, w.timestamp
            FROM weather w
            WHERE w.timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY w.timestamp DESC"""
            cursor.execute(query, (days,))
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            self.disconnect()
            
            if not data:
                logger.warning(f"⚠️ No data found")
                return None
            
            df = pd.DataFrame(data, columns=columns)
            logger.info(f"✅ Collected {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.disconnect()
            return None
    
    def validate_data(self, df):
        if df is None or len(df) == 0:
            return False
        min_records = 500
        if len(df) < min_records:
            logger.error(f"❌ Insufficient data: {len(df)} < {min_records}")
            return False
        logger.info("✅ Data validation passed")
        return True
    
    def save_data_to_csv(self, df, filename='data/training_data.csv'):
        try:
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
            df.to_csv(filename, index=False)
            logger.info(f"✅ Data saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
''')
logger.info("✅ Created data_collector.py")
