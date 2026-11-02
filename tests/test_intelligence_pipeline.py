import unittest

from intelligence.sensor_fusion import assess_situation


class TestIntelligencePipeline(unittest.TestCase):

    def test_valid_hazard_reading(self):
        data = {
            "gas_level": 450,
            "temperature": 30,
            "distance": 100,
        }

        result = assess_situation(data)

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_GAS_LEVEL", result["hazards"])

    def test_missing_gas_reading(self):
        data = {
            "gas_level": None,
            "temperature": 30,
            "distance": 100,
        }

        result = assess_situation(data)

        self.assertEqual(
            result["data_quality"]["gas_level"],
            "MISSING",
        )
        self.assertFalse(result["hazard_detected"])

    def test_invalid_gas_reading(self):
        data = {
            "gas_level": 5000,
            "temperature": 30,
            "distance": 100,
        }

        result = assess_situation(data)

        self.assertEqual(
            result["data_quality"]["gas_level"],
            "INVALID",
        )
        self.assertFalse(result["hazard_detected"])

    def test_non_numeric_temperature(self):
        data = {
            "gas_level": 100,
            "temperature": "hot",
            "distance": 100,
        }

        result = assess_situation(data)

        self.assertEqual(
            result["data_quality"]["temperature"],
            "INVALID",
        )
        self.assertFalse(result["hazard_detected"])

    def test_invalid_distance_does_not_trigger_obstacle(self):
        data = {
            "gas_level": 100,
            "temperature": 30,
            "distance": -5,
        }

        result = assess_situation(data)

        self.assertEqual(
            result["data_quality"]["distance"],
            "INVALID",
        )
        self.assertEqual(result["obstacles"], [])

    def test_multiple_conditions(self):
        data = {
            "gas_level": 450,
            "temperature": 55,
            "distance": 15,
        }

        result = assess_situation(data)

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_GAS_LEVEL", result["hazards"])
        self.assertIn("HIGH_TEMPERATURE", result["hazards"])
        self.assertIn("NEARBY_OBSTACLE", result["obstacles"])


if __name__ == "__main__":
    unittest.main()