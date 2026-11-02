import math


DEFAULT_THRESHOLDS = {
    "gas_level": 400,
    "temperature": 50,
    "distance": 20,
}

SENSOR_RANGES = {
    "gas_level": (0, 4095),
    "temperature": (-40, 125),
    "distance": (0, 400),
}


def validate_thresholds(thresholds=None):
    """Validate and return a complete threshold configuration."""
    config = DEFAULT_THRESHOLDS.copy()

    if thresholds is not None:
        if not isinstance(thresholds, dict):
            raise ValueError("Thresholds must be a dictionary.")

        unknown = set(thresholds) - set(DEFAULT_THRESHOLDS)
        if unknown:
            raise ValueError(
                f"Unknown threshold names: {sorted(unknown)}"
            )

        config.update(thresholds)

    for name, value in config.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(
                f"Threshold for {name} must be a finite number."
            )

        minimum, maximum = SENSOR_RANGES[name]

        if not minimum <= value <= maximum:
            raise ValueError(
                f"Threshold for {name} must be between "
                f"{minimum} and {maximum}."
            )

    return config


def assess_situation(sensor_data, thresholds=None):
    """Validate sensor readings and assess hazards and obstacles."""
    if not isinstance(sensor_data, dict):
        raise ValueError("Sensor data must be a dictionary.")

    config = validate_thresholds(thresholds)

    result = {
        "hazard_detected": False,
        "hazards": [],
        "obstacles": [],
        "data_quality": {},
    }

    valid_data = {}

    for name, value in sensor_data.items():
        if name not in SENSOR_RANGES:
            result["data_quality"][name] = "UNKNOWN_SENSOR"
            continue

        if value is None:
            result["data_quality"][name] = "MISSING"
            continue

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            result["data_quality"][name] = "INVALID"
            continue

        minimum, maximum = SENSOR_RANGES[name]

        if not minimum <= value <= maximum:
            result["data_quality"][name] = "INVALID"
            continue

        valid_data[name] = value
        result["data_quality"][name] = "VALID"

    gas_level = valid_data.get("gas_level")
    if gas_level is not None and gas_level > config["gas_level"]:
        result["hazard_detected"] = True
        result["hazards"].append("HIGH_GAS_LEVEL")

    temperature = valid_data.get("temperature")
    if (
        temperature is not None
        and temperature > config["temperature"]
    ):
        result["hazard_detected"] = True
        result["hazards"].append("HIGH_TEMPERATURE")

    distance = valid_data.get("distance")
    if distance is not None and distance < config["distance"]:
        result["obstacles"].append("NEARBY_OBSTACLE")

    # Summary fields for downstream reporting and dashboards.
    expected = set(SENSOR_RANGES)
    received = set(sensor_data)
    quality_values = result["data_quality"].values()

    result["summary"] = {
        "sensors_expected": len(expected),
        "sensors_received": len(expected & received),
        "sensors_valid": sum(
            result["data_quality"].get(name) == "VALID"
            for name in expected
        ),
        "sensors_missing": sum(
            result["data_quality"].get(name) == "MISSING"
            for name in expected
        ),
        "sensors_invalid": sum(
            result["data_quality"].get(name) == "INVALID"
            for name in expected
        ),
        "unknown_sensors": sum(
            status == "UNKNOWN_SENSOR"
            for status in quality_values
        ),
        "obstacle_detected": bool(result["obstacles"]),
        "assessment_status": (
            "HAZARD_DETECTED"
            if result["hazard_detected"]
            else "NO_HAZARD_DETECTED"
        ),
    }

    return result


if __name__ == "__main__":
    example = {
        "gas_level": 450,
        "temperature": 30,
        "distance": 15,
    }

    print("Sensor Intelligence Report:")
    print(assess_situation(example))