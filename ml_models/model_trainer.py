import os
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
        report = classification_report(
            y_test, y_pred, labels=[0, 1, 2, 3], target_names=class_names,
            zero_division=0, output_dict=True
        )
        logger.info(f"Classification Report:\n{report}")
        
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")
        
        return {
            "accuracy": accuracy,
            "classification_report": report,
            "confusion_matrix": cm.tolist(),
            "y_pred": y_pred,
            "y_pred_probs": y_pred_probs,
        }
    
    def save_model(self, model_path):
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.model.save(model_path)
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
