import json
import socket
import subprocess
import sys
import threading
import time
import unittest


class UDPReceiverIntegrationTests(unittest.TestCase):

    def setUp(self):
        """Start a fresh UDP receiver for each test."""
        self.receiver = None
        self.reader_thread = None
        self.output_lines = []
        self.output_lock = threading.Lock()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]

        self.receiver = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "intelligence.udp_receiver",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self.reader_thread = threading.Thread(
            target=self._read_receiver_output,
            daemon=True,
        )
        self.reader_thread.start()

        deadline = time.monotonic() + 5

        while time.monotonic() < deadline:
            if self.receiver.poll() is not None:
                self.fail("UDP receiver exited before startup.")

            with self.output_lock:
                output = "\n".join(self.output_lines)

            if f"Listening on 127.0.0.1:{self.port}" in output:
                return

            time.sleep(0.05)

        self.fail("UDP receiver did not start listening in time.")

    def tearDown(self):
        """Stop the receiver and clean up its resources."""
        self.stop_receiver()

    def _read_receiver_output(self):
        """Read subprocess output in the background."""
        receiver = self.receiver

        if receiver is None or receiver.stdout is None:
            return

        try:
            for line in receiver.stdout:
                with self.output_lock:
                    self.output_lines.append(line.rstrip("\r\n"))
        except (ValueError, OSError):
            pass

    def stop_receiver(self):
        """Terminate the receiver and close stdout."""
        receiver = self.receiver

        if receiver is None:
            return

        try:
            if receiver.poll() is None:
                receiver.terminate()

                try:
                    receiver.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    receiver.kill()
                    receiver.wait(timeout=3)
        finally:
            if self.reader_thread is not None:
                self.reader_thread.join(timeout=1)

            if receiver.stdout is not None and not receiver.stdout.closed:
                receiver.stdout.close()

            self.receiver = None

    def make_packet(
        self,
        sequence,
        gas_level=100,
        temperature=30,
        distance=100,
    ):
        """Create a packet using the project's actual sensor names."""
        timestamp = time.monotonic()

        return {
            "sequence": sequence,
            "timestamp": timestamp,
            "sensors": {
                "gas_level": gas_level,
                "temperature": temperature,
                "distance": distance,
            },
            "sensor_timestamps": {
                "gas_level": timestamp,
                "temperature": timestamp,
                "distance": timestamp,
            },
        }

    def send_packet(self, packet):
        """Send a packet to the UDP receiver."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(
                json.dumps(packet, allow_nan=False).encode("utf-8"),
                ("127.0.0.1", self.port),
            )

    def read_json_output(self, start_index, timeout=3):
        """Wait for the next complete JSON result."""
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            with self.output_lock:
                lines = self.output_lines[start_index:]

            for index, line in enumerate(lines):
                if not line.strip().startswith("{"):
                    continue

                candidate = [line]
                brace_count = line.count("{") - line.count("}")

                next_index = index + 1

                while brace_count > 0 and next_index < len(lines):
                    next_line = lines[next_index]
                    candidate.append(next_line)
                    brace_count += (
                        next_line.count("{") - next_line.count("}")
                    )
                    next_index += 1

                if brace_count == 0:
                    try:
                        result = json.loads("\n".join(candidate))
                        return result, start_index + next_index
                    except json.JSONDecodeError:
                        continue

            if self.receiver is not None and self.receiver.poll() is not None:
                self.fail("UDP receiver exited unexpectedly.")

            time.sleep(0.02)

        with self.output_lock:
            output = "\n".join(self.output_lines)

        self.fail(
            "Timed out waiting for JSON receiver output.\n"
            f"Receiver output:\n{output}"
        )

    def test_real_receiver_detects_gas_and_obstacle(self):
        """Verify high gas and nearby-obstacle detection."""
        packet = self.make_packet(
            sequence=1,
            gas_level=450,
            temperature=30,
            distance=15,
        )

        with self.output_lock:
            start_index = len(self.output_lines)

        self.send_packet(packet)
        result, _ = self.read_json_output(start_index)

        self.assertEqual(
            result.get("status"),
            "PROCESSED",
            msg=f"Unexpected receiver result: {result}",
        )
        self.assertEqual(result.get("sequence"), 1)

        assessment = result.get("assessment")
        self.assertIsInstance(assessment, dict)

        self.assertTrue(
            assessment.get("hazard_detected"),
            msg=f"No hazard detected in assessment: {assessment}",
        )

        self.assertTrue(
            assessment.get("hazards"),
            msg=f"No gas hazard reported: {assessment}",
        )

        self.assertTrue(
            assessment.get("obstacles"),
            msg=f"No obstacle reported: {assessment}",
        )

        data_quality = assessment.get("data_quality", {})

        self.assertTrue(
            all(
                data_quality.get(name) == "VALID"
                for name in ("gas_level", "temperature", "distance")
            ),
            msg=f"Unexpected data quality: {data_quality}",
        )

    def test_duplicate_packet_is_rejected_and_next_sequence_recovers(self):
        """Verify duplicate rejection and recovery with a new sequence."""
        first_packet = self.make_packet(
            sequence=101,
            gas_level=100,
            temperature=30,
            distance=100,
        )

        with self.output_lock:
            start_index = len(self.output_lines)

        self.send_packet(first_packet)
        first_result, _ = self.read_json_output(start_index)

        self.assertEqual(first_result.get("status"), "PROCESSED")
        self.assertEqual(first_result.get("sequence"), 101)

        with self.output_lock:
            start_index = len(self.output_lines)

        self.send_packet(first_packet)
        duplicate_result, _ = self.read_json_output(start_index)

        self.assertEqual(
            duplicate_result.get("status"),
            "DUPLICATE_OR_OUT_OF_ORDER_PACKET",
        )
        self.assertEqual(duplicate_result.get("sequence"), 101)
        self.assertEqual(
            duplicate_result.get("last_accepted_sequence"),
            101,
        )

        next_packet = self.make_packet(
            sequence=102,
            gas_level=100,
            temperature=30,
            distance=100,
        )

        with self.output_lock:
            start_index = len(self.output_lines)

        self.send_packet(next_packet)
        next_result, _ = self.read_json_output(start_index)

        self.assertEqual(next_result.get("status"), "PROCESSED")
        self.assertEqual(next_result.get("sequence"), 102)


if __name__ == "__main__":
    unittest.main()

