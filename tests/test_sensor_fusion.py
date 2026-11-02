import unittest

from intelligence.sensor_fusion import assess_situation, validate_thresholds


class TestSensorFusion(unittest.TestCase):

    def test_high_gas_level_detected(self):
        result = assess_situation({
            "gas_level": 450,
            "temperature": 30,
            "distance": 100,
        })

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_GAS_LEVEL", result["hazards"])

    def test_high_temperature_detected(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 60,
            "distance": 100,
        })

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_TEMPERATURE", result["hazards"])

    def test_nearby_obstacle_detected(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": 15,
        })

        self.assertIn("NEARBY_OBSTACLE", result["obstacles"])

    def test_no_hazard_or_obstacle(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": 100,
        })

        self.assertFalse(result["hazard_detected"])
        self.assertEqual(result["hazards"], [])
        self.assertEqual(result["obstacles"], [])

    def test_all_valid_readings_marked_valid(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": 100,
        })

        self.assertEqual(result["data_quality"]["gas_level"], "VALID")
        self.assertEqual(result["data_quality"]["temperature"], "VALID")
        self.assertEqual(result["data_quality"]["distance"], "VALID")

    def test_missing_gas_reading(self):
        result = assess_situation({
            "gas_level": None,
            "temperature": 30,
            "distance": 100,
        })

        self.assertEqual(result["data_quality"]["gas_level"], "MISSING")
        self.assertFalse(result["hazard_detected"])

    def test_missing_temperature_reading(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": None,
            "distance": 100,
        })

        self.assertEqual(
            result["data_quality"]["temperature"],
            "MISSING",
        )

    def test_missing_distance_reading(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": None,
        })

        self.assertEqual(result["data_quality"]["distance"], "MISSING")
        self.assertEqual(result["obstacles"], [])

    def test_invalid_string_reading(self):
        result = assess_situation({
            "gas_level": "invalid",
            "temperature": 30,
            "distance": 100,
        })

        self.assertEqual(result["data_quality"]["gas_level"], "INVALID")
        self.assertFalse(result["hazard_detected"])

    def test_invalid_boolean_reading(self):
        result = assess_situation({
            "gas_level": True,
            "temperature": 30,
            "distance": 100,
        })

        self.assertEqual(result["data_quality"]["gas_level"], "INVALID")

    def test_invalid_out_of_range_gas_reading(self):
        result = assess_situation({
            "gas_level": 5000,
            "temperature": 30,
            "distance": 100,
        })

        self.assertEqual(result["data_quality"]["gas_level"], "INVALID")
        self.assertFalse(result["hazard_detected"])

    def test_invalid_out_of_range_temperature(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 200,
            "distance": 100,
        })

        self.assertEqual(
            result["data_quality"]["temperature"],
            "INVALID",
        )

    def test_invalid_out_of_range_distance(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": 500,
        })

        self.assertEqual(result["data_quality"]["distance"], "INVALID")
        self.assertEqual(result["obstacles"], [])

    def test_unknown_sensor_is_reported(self):
        result = assess_situation({
            "gas_level": 100,
            "temperature": 30,
            "distance": 100,
            "humidity": 50,
        })

        self.assertEqual(
            result["data_quality"]["humidity"],
            "UNKNOWN_SENSOR",
        )

    def test_custom_thresholds_detect_hazards(self):
        result = assess_situation(
            {
                "gas_level": 250,
                "temperature": 40,
                "distance": 100,
            },
            thresholds={
                "gas_level": 200,
                "temperature": 35,
                "distance": 20,
            },
        )

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_GAS_LEVEL", result["hazards"])
        self.assertIn("HIGH_TEMPERATURE", result["hazards"])

    def test_values_equal_to_threshold_do_not_trigger(self):
        result = assess_situation(
            {
                "gas_level": 400,
                "temperature": 50,
                "distance": 20,
            }
        )

        self.assertFalse(result["hazard_detected"])
        self.assertEqual(result["hazards"], [])
        self.assertEqual(result["obstacles"], [])

    def test_invalid_threshold_type_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_thresholds("invalid")

    def test_unknown_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_thresholds({"humidity": 50})

    def test_non_finite_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_thresholds({"gas_level": float("nan")})

    def test_out_of_range_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_thresholds({"gas_level": 5000})

    def test_boolean_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_thresholds({"gas_level": True})

    def test_non_dictionary_sensor_data_is_rejected(self):
        with self.assertRaises(ValueError):
            assess_situation([100, 30, 15])

    # New tests for the sensor summary.

    def test_summary_counts_all_valid_sensors(self):
        result = assess_situation({
            "gas_level": 450,
            "temperature": 30,
            "distance": 15,
        })

        summary = result["summary"]

        self.assertEqual(summary["sensors_expected"], 3)
        self.assertEqual(summary["sensors_received"], 3)
        self.assertEqual(summary["sensors_valid"], 3)
        self.assertEqual(summary["sensors_missing"], 0)
        self.assertEqual(summary["sensors_invalid"], 0)
        self.assertEqual(summary["unknown_sensors"], 0)
        self.assertTrue(summary["obstacle_detected"])
        self.assertEqual(
            summary["assessment_status"],
            "HAZARD_DETECTED",
        )

    def test_summary_counts_missing_sensor(self):
        result = assess_situation({
            "gas_level": None,
            "temperature": 30,
            "distance": 100,
        })

        summary = result["summary"]

        self.assertEqual(summary["sensors_missing"], 1)
        self.assertEqual(summary["sensors_valid"], 2)
        self.assertEqual(summary["sensors_invalid"], 0)
        self.assertFalse(result["hazard_detected"])

    def test_summary_counts_invalid_sensor(self):
        result = assess_situation({
            "gas_level": "invalid",
            "temperature": 30,
            "distance": 100,
        })

        summary = result["summary"]

        self.assertEqual(summary["sensors_invalid"], 1)
        self.assertEqual(summary["sensors_valid"], 2)
        self.assertEqual(summary["sensors_missing"], 0)
        self.assertFalse(result["hazard_detected"])


if __name__ == "__main__":
    unittest.main()