from pymavlink import mavutil
import math

connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14551"
)

print("Waiting for heartbeat...")

connection.wait_heartbeat()

print("Heartbeat received!")

message = connection.recv_match(
    type="ATTITUDE",
    blocking=True
)

roll = message.roll
pitch = message.pitch
yaw = message.yaw

roll_degrees = math.degrees(roll)
pitch_degrees = math.degrees(pitch)
yaw_degrees = math.degrees(yaw)

print("Roll:", roll_degrees, "degrees")
print("Pitch:", pitch_degrees, "degrees")
print("Yaw:", yaw_degrees, "degrees")