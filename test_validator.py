from intelligence.data_validator import validate_data

drone_data = {
    "roll": 0.07,
    "latitude": -35.3633516,
    "battery_voltage": 12.6,
    "temperature": None
}

last_update = {
    "ATTITUDE": 98.5,
    "GPS": 94.0
}

current_time = 100.0

result = validate_data(drone_data, last_update, current_time)

print(result)