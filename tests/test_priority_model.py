import unittest

from intelligence.priority_model import (
    FEATURE_NAMES,
    predict_priority,
)


class TestPriorityModel(unittest.TestCase):
    def valid_features(self):
        return {
            "gas_level": 100,
            "temperature": 25,
            "distance": 100,
            "sensors_valid": 3,
            "sensors_missing": 0,
            "sensors_stale": 0,
            "obstacle_detected": 0,
            "hazard_detected": 0,
            "cv_person_detected": 0,
            "cv_confidence": 0.0,
        }

    def test_requires_all_features(self):
        with self.assertRaises(ValueError):
            predict_priority({"gas_level": 100})

    def test_rejects_non_finite_feature(self):
        features = self.valid_features()
        features["gas_level"] = float("nan")

        with self.assertRaises(ValueError):
            predict_priority(features)

    def test_rejects_invalid_cv_confidence(self):
        features = self.valid_features()
        features["cv_confidence"] = 1.5

        with self.assertRaises(ValueError):
            predict_priority(features)

    def test_feature_schema_has_ten_features(self):
        self.assertEqual(len(FEATURE_NAMES), 10)

    def test_returns_advisory_result(self):
        result = predict_priority(self.valid_features())

        self.assertTrue(result["advisory_only"])
        self.assertIn(
            result["data_quality_confidence"],
            ["LOW", "MEDIUM", "HIGH"],
        )
        self.assertIn(
            result["status"],
            ["OK", "MODEL_NOT_TRAINED"],
        )

        if result["status"] == "OK":
            self.assertIn(
                result["priority"],
                ["LOW", "MEDIUM", "HIGH"],
            )
            self.assertGreaterEqual(
                result["model_confidence"], 0.0
            )
            self.assertLessEqual(
                result["model_confidence"], 1.0
            )

    def test_gas_hazard_with_nearby_obstacle_is_high_priority(self):
        features = self.valid_features()
        features.update({
            "gas_level": 450,
            "distance": 15,
            "obstacle_detected": 1,
            "hazard_detected": 1,
        })

        result = predict_priority(features)

        if result["status"] == "OK":
            self.assertEqual(result["priority"], "HIGH")


if __name__ == "__main__":
    unittest.main()