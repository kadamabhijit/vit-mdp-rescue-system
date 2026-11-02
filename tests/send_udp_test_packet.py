import argparse
import json
import socket
import time


def main():
    parser = argparse.ArgumentParser(
        description="Send a simulated sensor packet over UDP"
    )

    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--sequence", type=int, default=1)
    parser.add_argument("--gas", type=float, default=450)
    parser.add_argument("--temperature", type=float, default=30)
    parser.add_argument("--distance", type=float, default=15)

    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")

    if args.sequence < 0:
        parser.error("Sequence number cannot be negative")

    now = time.monotonic()

    sensors = {
        "gas_level": args.gas,
        "temperature": args.temperature,
        "distance": args.distance,
    }

    packet = {
        "sequence": args.sequence,
        "timestamp": now,
        "sensors": sensors,
        "sensor_timestamps": {
            name: now for name in sensors
        },
    }

    message = json.dumps(
        packet,
        allow_nan=False,
    ).encode("utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        sender.sendto(message, (args.host, args.port))

    print(f"Test packet sent to {args.host}:{args.port}")
    print(json.dumps(packet, indent=2))


if __name__ == "__main__":
    main()