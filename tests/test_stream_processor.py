import json
import time
import unittest

from intelligence.stream_processor import process_json_line


class TestStreamProcessor(unittest.TestCase):

    def test_valid_hazard_packet(self):
        now = time.monotonic()

        packet = {
            "timestamp": now,
            "sensors": {
                "gas_level": 450,
                "temperature": 30,
                "distance": 15
            },
            "sensor_timestamps": {
                "gas_level": now,
                "temperature": now,
                "distance": now
            }
        }

        result = process_json_line(json.dumps(packet))

        self.assertEqual(result["status"], "PROCESSED")
        self.assertTrue(result["assessment"]["hazard_detected"])
        self.assertIn(
            "NEARBY_OBSTACLE",
            result["assessment"]["obstacles"]
        )

    def test_invalid_json(self):
        result = process_json_line("{invalid json")

        self.assertEqual(result["status"], "INVALID_JSON")
        self.assertIsNone(result["assessment"])

    def test_json_list_rejected(self):
        result = process_json_line("[1, 2, 3]")

        self.assertEqual(result["status"], "INVALID_PACKET")
        self.assertIsNone(result["assessment"])

    def test_stale_sensor_reading(self):
        now = time.monotonic()

        packet = {
            "timestamp": now,
            "sensors": {
                "gas_level": 450,
                "temperature": 30,
                "distance": 100
            },
            "sensor_timestamps": {
                "gas_level": now - 10,
                "temperature": now,
                "distance": now
            }
        }

        result = process_json_line(json.dumps(packet))

        self.assertEqual(result["status"], "PROCESSED")
        self.assertEqual(
            result["assessment"]["data_quality"]["gas_level"],
            "STALE"
        )
        self.assertNotIn(
            "HIGH_GAS_LEVEL",
            result["assessment"]["hazards"]
        )


if __name__ == "__main__":
    unittest.main()