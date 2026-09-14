import os, sys, logging
from datetime import datetime

# Create train.py
with open('train.py', 'w', encoding='utf-8') as f:
    f.write('''import os, sys, logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.data_collector import DataCollector
from ml_models.data_preprocessor import DataPreprocessor
from ml_models.model_trainer import ModelTrainer
from config import ML_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_directories():
    os.makedirs("data", exist_ok=True)
    os.makedirs(ML_CONFIG["model_dir"], exist_ok=True)
    logger.info("Directories created")

def collect_data():
    logger.info("\\n" + "="*60)
    logger.info("STEP 1: COLLECTING HISTORICAL DATA")
    logger.info("="*60)
    
    collector = DataCollector()
    
    lookback_days = ML_CONFIG["data"]["lookback_days"]
    logger.info(f"Collecting {lookback_days} days of historical data...")
    
    df = collector.collect_weather_data(days=lookback_days)
    
    if df is None:
        logger.error("Failed to collect data")
        logger.info("\\nTIPS:")
        logger.info("   - Make sure PostgreSQL is running")
        logger.info("   - Verify database has weather data")
        logger.info("   - Check DB_CONFIG in config.py")
        return False
    
    if not collector.validate_data(df):
        logger.error("Data validation failed")
        return False
    
    csv_path = "data/training_data.csv"
    collector.save_data_to_csv(df, csv_path)
    
    logger.info(f"Data collected: {len(df)} records")
    logger.info(f"   Saved to: {csv_path}")
    
    return csv_path

def prepare_data(csv_path):
    logger.info("\\n" + "="*60)
    logger.info("STEP 2: PREPARING DATA")
    logger.info("="*60)
    
    if not os.path.exists(csv_path):
        logger.error(f"Data file not found: {csv_path}")
        return False
    
    preprocessor = DataPreprocessor()
    result = preprocessor.prepare_data(csv_path, test_split=0.2)
    
    if result is None:
        logger.error("Data preparation failed")
        return False
    
    X_train, X_test, y_train, y_test, scaler, feature_names = result
    
    logger.info("Data preparation complete")
    logger.info(f"   Training set shape: {X_train.shape}")
    logger.info(f"   Test set shape: {X_test.shape}")
    
    return X_train, X_test, y_train, y_test, scaler, feature_names

def train_model(X_train, X_test, y_train, y_test, scaler, feature_names):
    logger.info("\\n" + "="*60)
    logger.info("STEP 3: TRAINING MODEL")
    logger.info("="*60)
    
    trainer = ModelTrainer()
    
    trainer.model = trainer.build_model(X_train.shape[1])
    
    trainer.train_model(X_train, y_train, X_test, y_test)
    
    eval_results = trainer.evaluate_model(X_test, y_test)
    
    import pickle
    
    os.makedirs(ML_CONFIG["model_dir"], exist_ok=True)
    
    trainer.save_model(ML_CONFIG["classifier_model_path"])
    
    scaler.save_scaler(ML_CONFIG["scaler_path"])
    
    with open(ML_CONFIG["feature_names_path"], "wb") as f:
        pickle.dump(feature_names, f)
    
    logger.info("Model trained and saved")
    logger.info(f"   Model path: {ML_CONFIG[\"classifier_model_path\"]}")
    logger.info(f"   Accuracy: {eval_results[\"accuracy\"]:.4f}")
    
    return True

def test_model():
    logger.info("\\n" + "="*60)
    logger.info("STEP 4: TESTING MODEL")
    logger.info("="*60)
    
    try:
        from ml_models.model_inference import ModelInference
        
        inference = ModelInference()
        
        test_cases = [
            {
                "name": "Normal Weather",
                "data": {"temperature": 25, "humidity": 60, "wind_speed": 8, "pressure": 1013, "hour": 14, "month": 6}
            },
            {
                "name": "High Humidity",
                "data": {"temperature": 28, "humidity": 88, "wind_speed": 12, "pressure": 1012, "hour": 14, "month": 6}
            },
            {
                "name": "Strong Wind",
                "data": {"temperature": 20, "humidity": 75, "wind_speed": 22, "pressure": 1008, "hour": 14, "month": 6}
            },
            {
                "name": "Critical Conditions",
                "data": {"temperature": 35, "humidity": 92, "wind_speed": 25, "pressure": 1005, "hour": 14, "month": 6}
            }
        ]
        
        logger.info("\\nTest Results:")
        logger.info("-" * 60)
        
        for test_case in test_cases:
            result = inference.predict(test_case["data"])
            if result:
                logger.info(f"{test_case['name']:20} -> {result['alert_level']:10} (confidence: {result['confidence']:.2%})")
        
        logger.info("-" * 60)
        logger.info("Model testing complete")
        
    except Exception as e:
        logger.error(f"Model testing failed: {e}")
        logger.info("   This is expected if model hasn't been trained yet")

def main():
    logger.info("\\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + "COASTAL THREAT ALERT - ML MODEL TRAINING".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")
    
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"GPU Support: {'Enabled' if ML_CONFIG['use_gpu'] else 'Disabled'}")
    logger.info(f"Model Type: {ML_CONFIG['model_type']}")
    
    create_directories()
    
    csv_path = collect_data()
    if not csv_path:
        logger.error("Cannot proceed without data")
        return False
    
    prep_result = prepare_data(csv_path)
    if not prep_result:
        logger.error("Cannot proceed with invalid data")
        return False
    
    X_train, X_test, y_train, y_test, scaler, feature_names = prep_result
    
    if not train_model(X_train, X_test, y_train, y_test, scaler, feature_names):
        logger.error("Model training failed")
        return False
    
    test_model()
    
    logger.info("\\n" + "="*60)
    logger.info("TRAINING PIPELINE COMPLETE!")
    logger.info("="*60)
    
    logger.info("\\nNEXT STEPS:")
    logger.info("   1. Update config.py: Set 'use_model': True")
    logger.info("   2. Restart the Flask app")
    logger.info("   3. Model will now be used for predictions")
    logger.info(f"\\nModel Location: {ML_CONFIG['classifier_model_path']}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\\nTraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\\nUnexpected error: {e}", exc_info=True)
        sys.exit(1)
''')

print("Created train.py")
