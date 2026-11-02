from pymavlink import mavutil

connection = mavutil.mavlink_connection(
    "udpin:127.0.0.1:14551"
)

print("Waiting for heartbeat...")
connection.wait_heartbeat()
print("Connected!")

print("Waiting for battery data...")

message = connection.recv_match(
    type="SYS_STATUS",
    blocking=True
)

voltage = message.voltage_battery / 1000
remaining = message.battery_remaining

print("Battery voltage:", voltage, "V")
print("Battery remaining:", remaining, "%")