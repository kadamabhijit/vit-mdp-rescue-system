import unittest

from intelligence.pipeline import process_sensor_packet


class TestSensorPipeline(unittest.TestCase):

    def setUp(self):
        self.current_time = 100.0

        self.sensor_data = {
            "gas_level": 450,
            "temperature": 30,
            "distance": 15,
        }

        self.timestamps = {
            "gas_level": 99.8,
            "temperature": 99.9,
            "distance": 99.7,
        }

    def test_fresh_gas_reading_detects_hazard(self):
        result = process_sensor_packet(
            self.sensor_data,
            self.timestamps,
            self.current_time,
        )

        self.assertTrue(result["hazard_detected"])
        self.assertIn("HIGH_GAS_LEVEL", result["hazards"])

    def test_fresh_nearby_obstacle_is_detected(self):
        result = process_sensor_packet(
            self.sensor_data,
            self.timestamps,
            self.current_time,
        )

        self.assertTrue(result["summary"]["obstacle_detected"])
        self.assertIn("NEARBY_OBSTACLE", result["obstacles"])

    def test_stale_gas_reading_is_excluded(self):
        timestamps = self.timestamps.copy()
        timestamps["gas_level"] = 90.0

        result = process_sensor_packet(
            self.sensor_data,
            timestamps,
            self.current_time,
        )

        self.assertEqual(result["data_quality"]["gas_level"], "STALE")
        self.assertNotIn("HIGH_GAS_LEVEL", result["hazards"])
        self.assertEqual(result["summary"]["sensors_stale"], 1)
        self.assertEqual(result["summary"]["data_quality_status"], "DEGRADED")

    def test_future_timestamp_is_rejected(self):
        timestamps = self.timestamps.copy()
        timestamps["gas_level"] = 101.0

        result = process_sensor_packet(
            self.sensor_data,
            timestamps,
            self.current_time,
        )

        self.assertEqual(
            result["data_quality"]["gas_level"],
            "INVALID_TIMESTAMP",
        )
        self.assertEqual(
            result["summary"]["sensors_invalid_timestamp"],
            1,
        )

    def test_missing_sensor_reading_is_detected(self):
        data = self.sensor_data.copy()
        data["gas_level"] = None

        result = process_sensor_packet(
            data,
            self.timestamps,
            self.current_time,
        )

        self.assertEqual(result["data_quality"]["gas_level"], "MISSING")
        self.assertEqual(result["summary"]["sensors_missing"], 1)
        self.assertEqual(result["summary"]["data_quality_status"], "DEGRADED")

    def test_missing_timestamp_is_detected(self):
        timestamps = self.timestamps.copy()
        del timestamps["gas_level"]

        result = process_sensor_packet(
            self.sensor_data,
            timestamps,
            self.current_time,
        )

        self.assertEqual(
            result["data_quality"]["gas_level"],
            "MISSING_TIMESTAMP",
        )
        self.assertEqual(
            result["summary"]["sensors_missing_timestamp"],
            1,
        )

    def test_invalid_sensor_value_is_counted(self):
        data = self.sensor_data.copy()
        data["gas_level"] = "invalid"

        result = process_sensor_packet(
            data,
            self.timestamps,
            self.current_time,
        )

        self.assertEqual(result["data_quality"]["gas_level"], "INVALID")
        self.assertEqual(result["summary"]["sensors_invalid"], 1)
        self.assertNotIn("HIGH_GAS_LEVEL", result["hazards"])

    def test_all_fresh_valid_readings_have_good_quality(self):
        result = process_sensor_packet(
            self.sensor_data,
            self.timestamps,
            self.current_time,
        )

        summary = result["summary"]

        self.assertEqual(summary["sensors_expected"], 3)
        self.assertEqual(summary["sensors_received"], 3)
        self.assertEqual(summary["sensors_valid"], 3)
        self.assertEqual(summary["sensors_stale"], 0)
        self.assertEqual(summary["sensors_invalid"], 0)
        self.assertEqual(summary["data_quality_status"], "GOOD")

    def test_non_dictionary_sensor_data_is_rejected(self):
        with self.assertRaises(ValueError):
            process_sensor_packet(
                [],
                self.timestamps,
                self.current_time,
            )

    def test_invalid_current_time_is_rejected(self):
        with self.assertRaises(ValueError):
            process_sensor_packet(
                self.sensor_data,
                self.timestamps,
                float("nan"),
            )

    def test_negative_max_age_is_rejected(self):
        with self.assertRaises(ValueError):
            process_sensor_packet(
                self.sensor_data,
                self.timestamps,
                self.current_time,
                max_age=-1,
            )


if __name__ == "__main__":
    unittest.main()