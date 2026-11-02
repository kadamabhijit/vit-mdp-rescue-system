import unittest

from intelligence.sensor_packet import create_sensor_packet
from intelligence.process_packet import process_packet


class TestProcessPacket(unittest.TestCase):

    def test_valid_packet(self):
        now = 100.0

        packet = create_sensor_packet(
            gas_level=450,
            temperature=30,
            distance=15,
            timestamp=now,
            sensor_timestamps={
                "gas_level": now,
                "temperature": now,
                "distance": now,
            },
        )

        result = process_packet(packet, current_time=now)

        self.assertEqual(result["status"], "PROCESSED")
        self.assertTrue(result["assessment"]["hazard_detected"])
        self.assertIn(
            "NEARBY_OBSTACLE",
            result["assessment"]["obstacles"],
        )

    def test_stale_gas_reading(self):
        now = 100.0

        packet = create_sensor_packet(
            gas_level=450,
            temperature=30,
            distance=100,
            timestamp=now,
            sensor_timestamps={
                "gas_level": 90.0,
                "temperature": now,
                "distance": now,
            },
        )

        result = process_packet(packet, current_time=now)

        self.assertEqual(
            result["assessment"]["data_quality"]["gas_level"],
            "STALE",
        )
        self.assertNotIn(
            "HIGH_GAS_LEVEL",
            result["assessment"]["hazards"],
        )

    def test_invalid_packet(self):
        result = process_packet({"timestamp": 10})

        self.assertEqual(result["status"], "INVALID_PACKET")
        self.assertIsNone(result["assessment"])


if __name__ == "__main__":
    unittest.main()