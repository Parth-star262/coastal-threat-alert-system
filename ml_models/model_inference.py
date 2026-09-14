import numpy as np
import pickle
import logging
import os
from config import ML_CONFIG

logger = logging.getLogger(__name__)

class ModelInference:
    def __init__(self):
        self.model = None
        self.model_framework = None
        self.scaler = None
        self.feature_names = None
        self.load_model_and_artifacts()
    
    def load_model_and_artifacts(self):
        try:
            model_path = ML_CONFIG["classifier_model_path"]
            pytorch_path = model_path.rsplit(".", 1)[0] + ".pt"
            
            if os.path.exists(pytorch_path):
                import torch
                from ml_models.pytorch_trainer import CoastalAlertNet
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = CoastalAlertNet(input_dim=len(ML_CONFIG["model"]["input_features"]))
                model.load_state_dict(torch.load(pytorch_path, map_location=self.device))
                model.to(self.device)
                model.eval()
                self.model = model
                self.model_framework = "pytorch"
                logger.info(f"PyTorch Model loaded from {pytorch_path}")
            else:
                from tensorflow import keras
                self.model = keras.models.load_model(model_path)
                self.model_framework = "keras"
                logger.info(f"Keras Model loaded from {model_path}")
            
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
            values = [data_dict.get(fname) for fname in self.feature_names]
            if any(value is None for value in values):
                logger.warning("Missing required prediction feature")
                return None
            features = np.asarray([values], dtype=float)
            if not np.isfinite(features).all():
                logger.warning("Non-finite prediction feature")
                return None
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
            
            if self.model_framework == "pytorch":
                import torch
                with torch.no_grad():
                    inputs_t = torch.tensor(features_scaled, dtype=torch.float32).to(self.device)
                    outputs = self.model(inputs_t)
                    probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
                probabilities = probs
            else:
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
