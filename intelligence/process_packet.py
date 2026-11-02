import math
import time

from intelligence.sensor_packet import validate_sensor_packet
from intelligence.pipeline import process_sensor_packet


def _is_finite_number(value):
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def process_packet(packet, current_time=None, max_age=2.0):
    if not validate_sensor_packet(packet):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    if current_time is None:
        current_time = time.monotonic()

    if (
        not _is_finite_number(current_time)
        or not _is_finite_number(max_age)
        or max_age < 0
    ):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    cv_person_detected = packet.get(
        "cv_person_detected",
        False,
    )
    cv_confidence = packet.get("cv_confidence", 0.0)

    if not isinstance(cv_person_detected, bool):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    if (
        not _is_finite_number(cv_confidence)
        or not 0.0 <= cv_confidence <= 1.0
    ):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    try:
        assessment = process_sensor_packet(
            sensor_data=packet["sensors"],
            last_update=packet["sensor_timestamps"],
            current_time=current_time,
            max_age=max_age,
            cv_person_detected=cv_person_detected,
            cv_confidence=cv_confidence,
        )
    except (ValueError, TypeError, OverflowError):
        return {
            "status": "INVALID_PACKET",
            "assessment": None,
        }

    return {
        "status": "PROCESSED",
        "assessment": assessment,
    }


if __name__ == "__main__":
    now = time.monotonic()

    from intelligence.sensor_packet import create_sensor_packet

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

    print(process_packet(packet, current_time=now))