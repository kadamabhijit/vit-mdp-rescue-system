import math

from intelligence.priority_model import predict_priority
from intelligence.sensor_fusion import assess_situation, SENSOR_RANGES


EXPECTED_SENSORS = list(SENSOR_RANGES.keys())


def _is_finite_number(value):
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def process_sensor_packet(
    sensor_data,
    last_update,
    current_time,
    max_age=2.0,
    thresholds=None,
    cv_person_detected=False,
    cv_confidence=0.0,
):
    if not isinstance(sensor_data, dict):
        raise ValueError("sensor_data must be a dictionary.")

    if not isinstance(last_update, dict):
        raise ValueError("last_update must be a dictionary.")

    if not _is_finite_number(current_time):
        raise ValueError("current_time must be a finite number.")

    if not _is_finite_number(max_age) or max_age < 0:
        raise ValueError(
            "max_age must be a finite non-negative number."
        )

    if not isinstance(cv_person_detected, bool):
        raise ValueError("cv_person_detected must be a boolean.")

    if not _is_finite_number(cv_confidence):
        raise ValueError("cv_confidence must be a finite number.")

    if not 0.0 <= cv_confidence <= 1.0:
        raise ValueError("cv_confidence must be between 0 and 1.")

    result = {
        "hazard_detected": False,
        "hazards": [],
        "obstacles": [],
        "data_quality": {},
    }

    usable_data = {}

    quality_counts = {
        "VALID": 0,
        "MISSING": 0,
        "MISSING_TIMESTAMP": 0,
        "INVALID_TIMESTAMP": 0,
        "STALE": 0,
        "INVALID": 0,
    }

    for name in EXPECTED_SENSORS:

        if name not in sensor_data or sensor_data[name] is None:
            result["data_quality"][name] = "MISSING"
            quality_counts["MISSING"] += 1
            continue

        if name not in last_update or last_update[name] is None:
            result["data_quality"][name] = "MISSING_TIMESTAMP"
            quality_counts["MISSING_TIMESTAMP"] += 1
            continue

        timestamp = last_update[name]

        if not _is_finite_number(timestamp):
            result["data_quality"][name] = "INVALID_TIMESTAMP"
            quality_counts["INVALID_TIMESTAMP"] += 1
            continue

        age = current_time - timestamp

        if age < 0:
            result["data_quality"][name] = "INVALID_TIMESTAMP"
            quality_counts["INVALID_TIMESTAMP"] += 1
            continue

        if age > max_age:
            result["data_quality"][name] = "STALE"
            quality_counts["STALE"] += 1
            continue

        sensor_assessment = assess_situation(
            {name: sensor_data[name]},
            thresholds=thresholds,
        )

        sensor_status = sensor_assessment["data_quality"].get(
            name,
            "INVALID",
        )

        if sensor_status != "VALID":
            result["data_quality"][name] = sensor_status

            if sensor_status == "MISSING":
                quality_counts["MISSING"] += 1
            else:
                quality_counts["INVALID"] += 1

            continue

        usable_data[name] = sensor_data[name]
        result["data_quality"][name] = "VALID"
        quality_counts["VALID"] += 1

    assessment = assess_situation(
        usable_data,
        thresholds=thresholds,
    )

    result["hazard_detected"] = assessment["hazard_detected"]
    result["hazards"] = assessment["hazards"]
    result["obstacles"] = assessment["obstacles"]

    result["summary"] = {
        "sensors_expected": len(EXPECTED_SENSORS),
        "sensors_received": sum(
            name in sensor_data for name in EXPECTED_SENSORS
        ),
        "sensors_valid": quality_counts["VALID"],
        "sensors_missing": quality_counts["MISSING"],
        "sensors_missing_timestamp": quality_counts[
            "MISSING_TIMESTAMP"
        ],
        "sensors_invalid_timestamp": quality_counts[
            "INVALID_TIMESTAMP"
        ],
        "sensors_stale": quality_counts["STALE"],
        "sensors_invalid": quality_counts["INVALID"],
        "obstacle_detected": bool(result["obstacles"]),
        "assessment_status": (
            "HAZARD_DETECTED"
            if result["hazard_detected"]
            else "NO_HAZARD_DETECTED"
        ),
        "data_quality_status": (
            "GOOD"
            if quality_counts["VALID"] == len(EXPECTED_SENSORS)
            else "DEGRADED"
        ),
    }

    priority_features = {
        "gas_level": (
            usable_data.get("gas_level", 0)
        ),
        "temperature": (
            usable_data.get("temperature", 0)
        ),
        "distance": (
            usable_data.get("distance", 0)
        ),
        "sensors_valid": quality_counts["VALID"],
        "sensors_missing": (
            quality_counts["MISSING"]
            + quality_counts["MISSING_TIMESTAMP"]
            + quality_counts["INVALID_TIMESTAMP"]
            + quality_counts["INVALID"]
        ),
        "sensors_stale": quality_counts["STALE"],
        "obstacle_detected": int(bool(result["obstacles"])),
        "hazard_detected": int(result["hazard_detected"]),
        "cv_person_detected": int(cv_person_detected),
        "cv_confidence": float(cv_confidence),
    }

    result["priority_estimate"] = predict_priority(
        priority_features
    )

    return result


if __name__ == "__main__":
    now = 100.0

    example_data = {
        "gas_level": 450,
        "temperature": 30,
        "distance": 15,
    }

    example_timestamps = {
        "gas_level": 99.8,
        "temperature": 99.9,
        "distance": 99.7,
    }

    report = process_sensor_packet(
        sensor_data=example_data,
        last_update=example_timestamps,
        current_time=now,
        cv_person_detected=False,
        cv_confidence=0.0,
    )

    print("Sensor Intelligence Pipeline Report:")
    print(report)