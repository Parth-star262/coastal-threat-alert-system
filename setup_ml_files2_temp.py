import os, logging

# Create model_trainer.py
with open('ml_models/model_trainer.py', 'w', encoding='utf-8') as f:
    f.write('''import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import logging

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.history = None
        self.setup_gpu()
    
    def setup_gpu(self):
        try:
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                logger.info(f"Found {len(gpus)} GPU device(s)")
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info("GPU configured")
            else:
                logger.warning("No GPU found, using CPU")
        except Exception as e:
            logger.error(f"GPU setup failed: {e}")
    
    def build_model(self, input_dim):
        model = keras.Sequential([
            layers.Input(shape=(input_dim,)),
            layers.Dense(64, activation="relu"),
            layers.Dropout(0.3),
            layers.BatchNormalization(),
            layers.Dense(32, activation="relu"),
            layers.Dropout(0.3),
            layers.BatchNormalization(),
            layers.Dense(4, activation="softmax")
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"]
        )
        
        logger.info("Model built successfully")
        return model
    
    def train_model(self, X_train, y_train, X_val=None, y_val=None):
        early_stopping = keras.callbacks.EarlyStopping(
            monitor="val_loss" if X_val is not None else "loss",
            patience=5,
            restore_best_weights=True
        )
        
        if X_val is not None:
            logger.info("Training model with validation...")
            self.history = self.model.fit(
                X_train, y_train,
                batch_size=32,
                epochs=50,
                validation_data=(X_val, y_val),
                callbacks=[early_stopping],
                verbose=1
            )
        else:
            logger.info("Training model without validation...")
            self.history = self.model.fit(
                X_train, y_train,
                batch_size=32,
                epochs=50,
                validation_split=0.15,
                callbacks=[early_stopping],
                verbose=1
            )
        
        logger.info("Model training complete")
        return self.history
    
    def evaluate_model(self, X_test, y_test):
        y_pred_probs = self.model.predict(X_test)
        y_pred = np.argmax(y_pred_probs, axis=1)
        
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        class_names = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        report = classification_report(y_test, y_pred, target_names=class_names)
        logger.info(f"Classification Report:\\n{report}")
        
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"Confusion Matrix:\\n{cm}")
        
        return {"accuracy": accuracy, "y_pred": y_pred, "y_pred_probs": y_pred_probs}
    
    def save_model(self, model_path):
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.model.save(model_path)
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
''')

# Create model_inference.py
with open('ml_models/model_inference.py', 'w', encoding='utf-8') as f:
    f.write('''import numpy as np
import pickle
import logging
from tensorflow import keras
from config import ML_CONFIG

logger = logging.getLogger(__name__)

class ModelInference:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.load_model_and_artifacts()
    
    def load_model_and_artifacts(self):
        try:
            self.model = keras.models.load_model(
                ML_CONFIG["classifier_model_path"]
            )
            logger.info("Model loaded")
            
            with open(ML_CONFIG["scaler_path"], "rb") as f:
                self.scaler = pickle.load(f)
            logger.info("Scaler loaded")
            
            with open(ML_CONFIG["feature_names_path"], "rb") as f:
                self.feature_names = pickle.load(f)
            logger.info("Feature names loaded")
            
            return True
        except Exception as e:
            logger.error(f"Error loading model artifacts: {e}")
            return False
    
    def prepare_input(self, data_dict):
        try:
            features = np.array([[data_dict.get(fname, 0) for fname in self.feature_names]])
            features_scaled = self.scaler.transform(features)
            return features_scaled
        except Exception as e:
            logger.error(f"Error preparing input: {e}")
            return None
    
    def predict(self, data_dict, return_confidence=True):
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            features_scaled = self.prepare_input(data_dict)
            if features_scaled is None:
                return None
            
            probabilities = self.model.predict(features_scaled, verbose=0)[0]
            alert_class = np.argmax(probabilities)
            confidence = float(probabilities[alert_class])
            
            alert_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            alert_level = alert_levels[alert_class]
            
            result = {
                "alert_level": alert_level,
                "alert_class": int(alert_class),
                "confidence": float(confidence),
                "weather_data": data_dict
            }
            
            if return_confidence:
                result["all_probabilities"] = {
                    level: float(prob)
                    for level, prob in zip(alert_levels, probabilities)
                }
            
            logger.info(f"Prediction: {alert_level} (confidence: {confidence:.2%})")
            
            return result
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return None
    
    def predict_with_fallback(self, data_dict):
        prediction = self.predict(data_dict)
        
        if prediction:
            prediction["source"] = "model"
            return prediction
        
        logger.warning("Falling back to threshold-based alerts")
        from config import ALERT_THRESHOLDS
        
        wind_speed = data_dict.get("wind_speed", 0)
        humidity = data_dict.get("humidity", 0)
        
        if wind_speed > ALERT_THRESHOLDS["wind_speed_high"] or humidity > ALERT_THRESHOLDS["humidity_high"]:
            alert_level = "CRITICAL"
        elif wind_speed > ALERT_THRESHOLDS["wind_speed_medium"] or humidity > ALERT_THRESHOLDS["humidity_medium"]:
            alert_level = "HIGH"
        else:
            alert_level = "LOW"
        
        return {
            "alert_level": alert_level,
            "source": "fallback",
            "weather_data": data_dict
        }
''')

print("Created model_trainer.py and model_inference.py")
