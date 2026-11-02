from pymavlink import mavutil

connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14551"
)

print("Waiting for heartbeat...")
connection.wait_heartbeat()
print("Connected!")

print("Waiting for GPS data...")

message = connection.recv_match(
    type="GLOBAL_POSITION_INT",
    blocking=True
)

latitude = message.lat / 10000000
longitude = message.lon / 10000000
altitude = message.relative_alt / 1000

print("Latitude:", latitude)
print("Longitude:", longitude)
print("Altitude:", altitude, "metres")