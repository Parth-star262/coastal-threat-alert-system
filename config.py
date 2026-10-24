import os
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv

load_dotenv("credentials.env")

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "5000"))
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

def _database_config():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        database_url = database_url.strip().strip("\"'")
        if database_url.startswith("DATABASE_URL="):
            database_url = database_url[len("DATABASE_URL="):].strip().strip("\"'")
        parsed = urlparse(database_url)
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or not parsed.hostname
            or not parsed.path.lstrip("/")
        ):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection URL")

        query = parse_qs(parsed.query)
        return {
            "host": parsed.hostname,
            "database": parsed.path.lstrip("/"),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "port": parsed.port or 5432,
            "sslmode": query.get("sslmode", [os.getenv("DB_SSLMODE", "require")])[0],
        }

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "weatherdb"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASS", ""),
        "port": os.getenv("DB_PORT", "5432"),
        "sslmode": os.getenv("DB_SSLMODE", "prefer"),
    }


DB_CONFIG = _database_config()

EMAIL_CONFIG = {
    "sender_email": os.getenv("GMAIL_USER"),
    "app_password": os.getenv("GMAIL_APP_PASSWORD"),
    "receiver_email": os.getenv("RECEIVER_EMAIL")
}

API_CONFIG = {
    "openweather_api_key": os.getenv("OPENWEATHER_API_KEY")
}

TWILIO_CONFIG = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
    "from_number": os.getenv("TWILIO_FROM_NUMBER"),
    "to_number": os.getenv("TWILIO_TO_NUMBER")
}

NOTIFICATION_TEST_MODE = os.getenv("NOTIFICATION_TEST_MODE", "false").lower() == "true"
NOTIFICATION_MAX_RETRIES = max(1, int(os.getenv("NOTIFICATION_MAX_RETRIES", "2")))

ALERT_THRESHOLDS = {
    "wind_speed_high": 20,
    "wind_speed_medium": 15,
    "humidity_high": 90,
    "humidity_medium": 85
}

COASTAL_LOCATIONS = {
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Visakhapatnam": (17.6865, 83.2185),
    "Surat": (21.1702, 72.8311),
    "Kochi": (9.9312, 76.2673),
    "Mangalore": (12.9716, 74.8604),
}

ML_CONFIG = {
    "model_dir": "ml_models/trained_models",
    "classifier_model_path": "ml_models/trained_models/alert_classifier.h5",
    "scaler_path": "ml_models/trained_models/scaler.pkl",
    "feature_names_path": "ml_models/trained_models/feature_names.pkl",
    "use_gpu": True,
    "gpu_id": 0,
    "batch_size": 32,
    "training": {
        "epochs": 50,
        "batch_size": 32,
        "validation_split": 0.15,
        "learning_rate": 0.001,
        "early_stopping_patience": 5,
        "test_split": 0.2
    },
    "model": {
        "input_features": ["temperature", "humidity", "wind_speed", "pressure", "hour", "month"],
        "output_classes": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "hidden_units": [64, 32],
        "dropout_rate": 0.3
    },
    "data": {
        "min_historical_records": 500,
        "lookback_days": 90,
    },
    "model_type": "classifier",
    "use_model": True
}

ALERT_CLASS_MAPPING = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH",
    3: "CRITICAL"
}
