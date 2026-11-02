import math
import time
from collections import deque


class SensorSynchronizer:
    def __init__(
        self,
        required_sensors,
        tolerance_ms=20.0,
        buffer_size=100,
    ):
        if not required_sensors:
            raise ValueError("At least one sensor is required.")

        if len(set(required_sensors)) != len(required_sensors):
            raise ValueError("Sensor names must be unique.")

        if not math.isfinite(tolerance_ms) or tolerance_ms < 0:
            raise ValueError("tolerance_ms must be finite and non-negative.")

        if buffer_size < 1:
            raise ValueError("buffer_size must be positive.")

        self.required_sensors = tuple(required_sensors)
        self.tolerance_s = tolerance_ms / 1000.0
        self.buffer_size = buffer_size
        self.buffers = {
            name: deque(maxlen=buffer_size)
            for name in self.required_sensors
        }

    def add(self, sensor, value, timestamp, received_at=None):
        if sensor not in self.buffers:
            raise ValueError(f"Unknown sensor: {sensor}")

        if isinstance(timestamp, bool) or not isinstance(
            timestamp, (int, float)
        ):
            raise ValueError("Timestamp must be numeric.")

        if not math.isfinite(timestamp):
            raise ValueError("Timestamp must be finite.")

        if received_at is None:
            received_at = time.monotonic()

        if not math.isfinite(received_at):
            raise ValueError("Receipt time must be finite.")

        buffer = self.buffers[sensor]

        if buffer and timestamp <= buffer[-1]["timestamp"]:
            return False

        buffer.append({
            "timestamp": float(timestamp),
            "received_at": float(received_at),
            "value": value,
        })

        return True

    def get_snapshot(self):
        if any(not self.buffers[name] for name in self.required_sensors):
            return None

        best = None

        for anchor_sensor in self.required_sensors:
            for anchor in self.buffers[anchor_sensor]:
                selected = {}
                timestamps = []

                for sensor in self.required_sensors:
                    candidates = [
                        item for item in self.buffers[sensor]
                        if abs(item["timestamp"] - anchor["timestamp"])
                        <= self.tolerance_s
                    ]

                    if not candidates:
                        break

                    nearest = min(
                        candidates,
                        key=lambda item: abs(
                            item["timestamp"] - anchor["timestamp"]
                        ),
                    )

                    selected[sensor] = nearest
                    timestamps.append(nearest["timestamp"])

                if len(selected) != len(self.required_sensors):
                    continue

                spread = max(timestamps) - min(timestamps)

                if spread > self.tolerance_s:
                    continue

                key = (
                    spread,
                    -max(timestamps),
                )

                if best is None or key < best[0]:
                    best = (key, selected, timestamps)

        if best is None:
            return None

        _, selected, timestamps = best

        snapshot = {
            "reference_timestamp": sum(timestamps) / len(timestamps),
            "timestamp_spread_ms": (
                max(timestamps) - min(timestamps)
            ) * 1000.0,
            "sensors": {
                name: item["value"]
                for name, item in selected.items()
            },
            "source_timestamps": {
                name: item["timestamp"]
                for name, item in selected.items()
            },
        }

        for name, item in selected.items():
            buffer = self.buffers[name]

            while buffer:
                consumed = buffer.popleft()

                if consumed is item:
                    break

        return snapshot