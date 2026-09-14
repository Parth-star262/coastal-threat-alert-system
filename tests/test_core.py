import unittest
from unittest.mock import Mock

from app import validate_weather_payload
from ml_models.model_inference import ModelInference
from services.risk_assessment_service import RiskAssessmentService


class CoreBehaviorTests(unittest.TestCase):
    def test_weather_payload_rejects_invalid_humidity(self):
        payload = {
            "city": "Mumbai",
            "temperature": 25,
            "humidity": 120,
            "wind_speed": 4,
            "description": "clear",
        }
        self.assertIn("humidity", validate_weather_payload(payload))

    def test_weather_payload_accepts_valid_record(self):
        payload = {
            "city": "Mumbai",
            "temperature": 25,
            "humidity": 70,
            "wind_speed": 4,
            "description": "clear",
        }
        self.assertIsNone(validate_weather_payload(payload))

    def test_risk_level_boundaries(self):
        self.assertEqual(RiskAssessmentService._risk_level(0), "LOW")
        self.assertEqual(RiskAssessmentService._risk_level(2), "MEDIUM")
        self.assertEqual(RiskAssessmentService._risk_level(4), "HIGH")
        self.assertEqual(RiskAssessmentService._risk_level(6), "CRITICAL")

    def test_distance_is_zero_for_same_location(self):
        distance = RiskAssessmentService._distance_km(19.0, 72.0, 19.0, 72.0)
        self.assertEqual(distance, 0)

    def test_missing_model_feature_uses_fallback(self):
        inference = ModelInference.__new__(ModelInference)
        inference.model = Mock()
        inference.feature_names = ["temperature", "pressure"]
        inference.scaler = Mock()
        result = inference.predict_with_fallback({"temperature": 25, "wind_speed": 25, "humidity": 60})
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["alert_level"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
