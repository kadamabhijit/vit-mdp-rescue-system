from pymavlink import mavutil
import math

connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14551"
)

print("Waiting for heartbeat...")
connection.wait_heartbeat()
print("Connected!")

drone_data = {}

message = connection.recv_match(
    type="ATTITUDE",
    blocking=True
)

drone_data["roll"] = round(math.degrees(message.roll), 2)
drone_data["pitch"] = round(math.degrees(message.pitch), 2)
drone_data["yaw"] = round(math.degrees(message.yaw), 2)

message = connection.recv_match(
    type="GLOBAL_POSITION_INT",
    blocking=True
)

drone_data["latitude"] = message.lat / 10000000
drone_data["longitude"] = message.lon / 10000000
drone_data["altitude"] = message.relative_alt / 1000

message = connection.recv_match(
    type="SYS_STATUS",
    blocking=True
)

drone_data["battery_voltage"] = message.voltage_battery / 1000
drone_data["battery_remaining"] = message.battery_remaining

print("\nDrone Status")
print(drone_data)