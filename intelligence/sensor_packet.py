import math
import time


EXPECTED_SENSORS = {
    "gas_level",
    "temperature",
    "distance",
}


def create_sensor_packet(
    gas_level=None,
    temperature=None,
    distance=None,
    timestamp=None,
    sensor_timestamps=None,
    sequence=None,
):
    if timestamp is None:
        timestamp = time.monotonic()

    if sensor_timestamps is None:
        sensor_timestamps = {}

    return {
        "sequence": sequence,
        "timestamp": timestamp,
        "sensors": {
            "gas_level": gas_level,
            "temperature": temperature,
            "distance": distance,
        },
        "sensor_timestamps": sensor_timestamps.copy(),
    }


def _is_finite_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def validate_sensor_packet(packet):
    if not isinstance(packet, dict):
        return False

    if not _is_finite_number(packet.get("timestamp")):
        return False

    sequence = packet.get("sequence")

    if sequence is not None:
        if (
            isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
        ):
            return False

    sensors = packet.get("sensors")
    sensor_timestamps = packet.get("sensor_timestamps")

    if not isinstance(sensors, dict):
        return False

    if not isinstance(sensor_timestamps, dict):
        return False

    # Reject unknown sensor names to catch protocol mismatches.
    if not set(sensors).issubset(EXPECTED_SENSORS):
        return False

    if not set(sensor_timestamps).issubset(EXPECTED_SENSORS):
        return False

    # Sensor values may be None when a reading is unavailable.
    for name, value in sensors.items():
        if value is not None and not _is_finite_number(value):
            return False

    # Timestamps may be absent for missing readings.
    for name, sensor_timestamp in sensor_timestamps.items():
        if sensor_timestamp is not None and not _is_finite_number(
            sensor_timestamp
        ):
            return False

    return True


if __name__ == "__main__":
    now = time.monotonic()

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
        sequence=1,
    )

    print("Sensor packet:")
    print(packet)
    print("Valid:", validate_sensor_packet(packet))