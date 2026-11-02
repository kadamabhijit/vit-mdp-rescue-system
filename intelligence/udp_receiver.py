import argparse
import json
import math
import socket
import time

from intelligence.sensor_packet import validate_sensor_packet
from intelligence.stream_processor import process_json_line


BUFFER_SIZE = 4096


def _is_finite_number(value):
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _translate_sensor_timestamps(packet, received_at):
    packet_timestamp = packet["timestamp"]
    sensor_timestamps = packet["sensor_timestamps"]

    translated = {}

    for name, sensor_timestamp in sensor_timestamps.items():
        if sensor_timestamp is None:
            translated[name] = None
            continue

        age = packet_timestamp - sensor_timestamp

        translated[name] = received_at - age

    return translated


def process_datagram(raw_data, address, last_sequences):
    try:
        message = raw_data.decode("utf-8").strip()
        packet = json.loads(message)

    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "status": "INVALID_JSON",
            "sequence": None,
            "assessment": None,
        }

    if not isinstance(packet, dict):
        return {
            "status": "INVALID_PACKET",
            "sequence": None,
            "assessment": None,
        }

    sequence = packet.get("sequence")

    if not validate_sensor_packet(packet):
        return {
            "status": "INVALID_PACKET",
            "sequence": sequence,
            "assessment": None,
        }

    sender_id = address[0]

    if sequence is not None:
        previous_sequence = last_sequences.get(sender_id)

        if (
            previous_sequence is not None
            and sequence <= previous_sequence
        ):
            return {
                "status": "DUPLICATE_OR_OUT_OF_ORDER_PACKET",
                "sequence": sequence,
                "last_accepted_sequence": previous_sequence,
                "assessment": None,
            }

    received_at = time.monotonic()

    processed_packet = dict(packet)
    processed_packet["timestamp"] = received_at

    try:
        processed_packet["sensor_timestamps"] = (
            _translate_sensor_timestamps(
                packet,
                received_at,
            )
        )

        processed_message = json.dumps(
            processed_packet,
            allow_nan=False,
        )

        result = process_json_line(processed_message)

    except (ValueError, TypeError, OverflowError):
        return {
            "status": "INVALID_PACKET",
            "sequence": sequence,
            "assessment": None,
        }

    if not isinstance(result, dict):
        return {
            "status": "PROCESSING_ERROR",
            "sequence": sequence,
            "assessment": None,
        }

    if (
        sequence is not None
        and result.get("status") == "PROCESSED"
    ):
        last_sequences[sender_id] = sequence

    result["sequence"] = sequence

    return result


def main():
    parser = argparse.ArgumentParser(
        description="UDP Sensor Intelligence Receiver"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="IP address to listen on",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5005,
        help="UDP port to listen on",
    )

    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535.")

    last_sequences = {}

    try:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        ) as server:
            server.bind((args.host, args.port))

            print(
                "UDP Sensor Intelligence Receiver",
                flush=True,
            )
            print(
                f"Listening on {args.host}:{args.port}",
                flush=True,
            )
            print(
                "Press Ctrl+C to stop.\n",
                flush=True,
            )

            while True:
                raw_data, address = server.recvfrom(BUFFER_SIZE)

                result = process_datagram(
                    raw_data,
                    address,
                    last_sequences,
                )

                print(
                    f"\nPacket received from {address}",
                    flush=True,
                )

                print(
                    json.dumps(
                        result,
                        indent=2,
                        allow_nan=False,
                    ),
                    flush=True,
                )

    except KeyboardInterrupt:
        print("\nUDP receiver stopped.", flush=True)

    except OSError as error:
        print(
            f"Receiver error: {error}",
            flush=True,
        )


if __name__ == "__main__":
    main()