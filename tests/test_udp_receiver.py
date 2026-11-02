import json
import socket
import subprocess
import sys
import time
import unittest


HOST = "127.0.0.1"
PORT = 0


class TestUDPReceiver(unittest.TestCase):

    def test_udp_packet_delivery(self):
        packet = {
            "timestamp": time.monotonic(),
            "sensors": {
                "gas_level": 450,
                "temperature": 30,
                "distance": 15
            },
            "sensor_timestamps": {}
        }

        now = time.monotonic()
        packet["timestamp"] = now
        packet["sensor_timestamps"] = {
            "gas_level": now,
            "temperature": now,
            "distance": now
        }

        with socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        ) as receiver:

            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(2.0)

            address = receiver.getsockname()

            with socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            ) as sender:

                sender.sendto(
                    json.dumps(packet).encode("utf-8"),
                    address
                )

            received_data, sender_address = receiver.recvfrom(4096)

        received_packet = json.loads(received_data.decode("utf-8"))

        self.assertEqual(
            received_packet["sensors"]["gas_level"],
            450
        )

        self.assertEqual(
            received_packet["sensors"]["distance"],
            15
        )

        self.assertIsNotNone(sender_address)


if __name__ == "__main__":
    unittest.main()