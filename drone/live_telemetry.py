from pymavlink import mavutil
import math
import time
from intelligence.data_validator import validate_data
# Connect to the drone's MAVLink data stream
connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14551"
)

print("Waiting for heartbeat...")

try:
    heartbeat = connection.wait_heartbeat(timeout=30)

    if heartbeat is None:
        raise TimeoutError("No heartbeat received within 30 seconds.")

    print("Connected!")

    # Store the latest drone readings
    drone_data = {
        "roll": None,
        "pitch": None,
        "yaw": None,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "battery_voltage": None,
        "battery_remaining": None
    }

    # Store the last reception time for each message type
    last_update = {}

    # Store the quality status of each message type
    data_quality = {}

    # Initial demonstration threshold, not a safety limit
    MAX_AGE = 2.0

    expected_messages = [
        "ATTITUDE",
        "GLOBAL_POSITION_INT",
        "SYS_STATUS"
    ]

    def check_data_freshness(last_update, now):
        status = {}

        for message_name in expected_messages:

            if message_name not in last_update:
                status[message_name] = "MISSING"

            else:
                age = now - last_update[message_name]

                if age <= MAX_AGE:
                    status[message_name] = "FRESH"
                else:
                    status[message_name] = "STALE"

        return status

    try:
        while True:

            # Wait for a telemetry message
            message = connection.recv_match(
                type=expected_messages,
                blocking=True,
                timeout=1
            )

            now = time.monotonic()

            if message is not None:

                message_type = message.get_type()

                # Update attitude
                if message_type == "ATTITUDE":
                    drone_data["roll"] = round(
                        math.degrees(message.roll), 2
                    )

                    drone_data["pitch"] = round(
                        math.degrees(message.pitch), 2
                    )

                    drone_data["yaw"] = round(
                        math.degrees(message.yaw), 2
                    )

                # Update GPS position and altitude
                elif message_type == "GLOBAL_POSITION_INT":
                    drone_data["latitude"] = (
                        message.lat / 10000000
                    )

                    drone_data["longitude"] = (
                        message.lon / 10000000
                    )

                    drone_data["altitude"] = (
                        message.relative_alt / 1000
                    )

                # Update battery information
                elif message_type == "SYS_STATUS":

                    if message.voltage_battery != 65535:
                        drone_data["battery_voltage"] = (
                            message.voltage_battery / 1000
                        )

                    if message.battery_remaining >= 0:
                        drone_data["battery_remaining"] = (
                            message.battery_remaining
                        )

                # Record the reception time
                last_update[message_type] = now

            # Recheck every message, even if nothing arrived
            data_quality = check_data_freshness(
                last_update, now
            )
            validation_result = validate_data(
                drone_data,
                last_update,
                now
            )
            print("\n--- VALIDATOR OUTPUT ---")
            print(validation_result)
            
            print("\n--- DRONE STATUS ---")

            for key, value in drone_data.items():
                print(key, ":", value)

            print("\n--- DATA QUALITY ---")

            for message_name in expected_messages:

                status = data_quality[message_name]

                if message_name in last_update:
                    age = now - last_update[message_name]

                    print(
                        message_name,
                        ":",
                        status,
                        "| Reception age:",
                        round(age, 2),
                        "seconds"
                    )

                else:
                    print(message_name, ":", status)

    except KeyboardInterrupt:
        print("\nTelemetry stopped by user.")

finally:
    connection.close()
    print("Connection closed.")
