import json
import math
import sys

from intelligence.process_packet import process_packet


def process_json_line(line):
    try:
        packet = json.loads(line)
    except json.JSONDecodeError:
        return {
            "status": "INVALID_JSON",
            "assessment": None,
        }

    if not isinstance(packet, dict):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    result = process_packet(packet)

    return result


def main():
    print("Live Sensor Intelligence Bridge")
    print("Waiting for JSON sensor packets...")
    print("Enter one JSON packet per line. Type 'exit' to stop.")
    print()

    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        if line.lower() == "exit":
            print("Sensor bridge stopped.")
            break

        result = process_json_line(line)

        print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()