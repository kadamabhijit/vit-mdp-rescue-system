def check_data(data):
    result = {}

    for name, value in data.items():
        if value is None:
            result[name] = "MISSING"
        else:
            result[name] = "AVAILABLE"

    return result


def check_freshness(last_update, current_time, max_age=2.0):
    result = {}

    for name, update_time in last_update.items():
        age = current_time - update_time

        if age < 0:
            result[name] = "INVALID_TIME"
        elif age <= max_age:
            result[name] = "FRESH"
        else:
            result[name] = "STALE"

    return result


def check_validity(data):
    result = {}

    valid_ranges = {
        "roll": (-180, 180),
        "pitch": (-90, 90),
        "yaw": (-180, 180),
        "latitude": (-90, 90),
        "longitude": (-180, 180),
        "battery_voltage": (0, 60),
        "battery_remaining": (0, 100)
    }

    for name, value in data.items():

        if value is None:
            result[name] = "MISSING"

        elif name in valid_ranges:
            minimum, maximum = valid_ranges[name]

            if minimum <= value <= maximum:
                result[name] = "VALID"
            else:
                result[name] = "INVALID"

        else:
            result[name] = "NOT_CHECKED"

    return result


def validate_data(data, last_update, current_time):
    result = {
        "availability": check_data(data),
        "freshness": check_freshness(last_update, current_time),
        "validity": check_validity(data)
    }

    return result


if __name__ == "__main__":

    drone_data = {
        "roll": 0.07,
        "pitch": -0.03,
        "yaw": 0.66,
        "latitude": -35.3633514,
        "longitude": 149.1652411,
        "altitude": -0.003,
        "battery_voltage": 12.6,
        "battery_remaining": 100,
        "temperature": None
    }

    last_update = {
        "ATTITUDE": 98.5,
        "GLOBAL_POSITION_INT": 99.8,
        "SYS_STATUS": 99.9
    }

    current_time = 100.0

    result = validate_data(
        drone_data,
        last_update,
        current_time
    )

    print(result)