import json
import unittest
from unittest.mock import patch

from intelligence.udp_receiver import process_datagram


class TestUDPReceiverLogic(unittest.TestCase):

    def setUp(self):
        self.last_sequences = {}
        self.address = ("127.0.0.1", 50634)

        self.packet = {
            "sequence": 1,
            "timestamp": 100.0,
            "sensors": {
                "gas_level": 450,
                "temperature": 30,
                "distance": 15,
            },
            "sensor_timestamps": {
                "gas_level": 100.0,
                "temperature": 100.0,
                "distance": 100.0,
            },
        }

    def send_packet(self, packet):
        raw_data = json.dumps(packet).encode("utf-8")
        return process_datagram(
            raw_data,
            self.address,
            self.last_sequences,
        )

    def test_valid_packet_is_processed(self):
        with patch(
            "intelligence.udp_receiver.process_json_line"
        ) as mock_process:
            mock_process.return_value = {
                "status": "PROCESSED",
                "assessment": {
                    "hazard_detected": True,
                    "hazards": ["HIGH_GAS_LEVEL"],
                    "obstacles": ["NEARBY_OBSTACLE"],
                },
            }

            result = self.send_packet(self.packet)

        self.assertEqual(result["status"], "PROCESSED")
        self.assertEqual(self.last_sequences["127.0.0.1"], 1)

    def test_malformed_json_is_rejected(self):
        result = process_datagram(
            b"{invalid-json",
            self.address,
            self.last_sequences,
        )

        self.assertEqual(result["status"], "INVALID_JSON")
        self.assertIsNone(result["assessment"])

    def test_invalid_packet_is_rejected(self):
        invalid_packet = {
            "timestamp": "not-a-number",
            "sensors": {},
            "sensor_timestamps": {},
        }

        result = self.send_packet(invalid_packet)

        self.assertEqual(result["status"], "INVALID_PACKET")
        self.assertIsNone(result["assessment"])

    def test_duplicate_sequence_is_rejected(self):
        self.last_sequences["127.0.0.1"] = 1

        result = self.send_packet(self.packet)

        self.assertEqual(
            result["status"],
            "DUPLICATE_OR_OUT_OF_ORDER_PACKET",
        )
        self.assertIsNone(result["assessment"])

    def test_out_of_order_sequence_is_rejected(self):
        self.last_sequences["127.0.0.1"] = 5
        self.packet["sequence"] = 3

        result = self.send_packet(self.packet)

        self.assertEqual(
            result["status"],
            "DUPLICATE_OR_OUT_OF_ORDER_PACKET",
        )
        self.assertIsNone(result["assessment"])

    def test_failed_processing_does_not_advance_sequence(self):
        with patch(
            "intelligence.udp_receiver.process_json_line"
        ) as mock_process:
            mock_process.return_value = {
                "status": "INVALID_PACKET",
                "assessment": None,
            }

            result = self.send_packet(self.packet)

        self.assertEqual(result["status"], "INVALID_PACKET")
        self.assertNotIn("127.0.0.1", self.last_sequences)


if __name__ == "__main__":
    unittest.main(verbosity=2)