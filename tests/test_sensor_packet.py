import unittest

from intelligence.sensor_packet import (
    create_sensor_packet,
    validate_sensor_packet,
)


class TestSensorPacket(unittest.TestCase):

    def test_packet_creation(self):
        packet = create_sensor_packet(
            gas_level=450,
            temperature=30,
            distance=15,
            sequence=1,
        )

        self.assertEqual(packet["sensors"]["gas_level"], 450)
        self.assertEqual(packet["sensors"]["temperature"], 30)
        self.assertEqual(packet["sensors"]["distance"], 15)
        self.assertEqual(packet["sequence"], 1)

    def test_valid_packet(self):
        packet = create_sensor_packet(
            gas_level=450,
            temperature=30,
            distance=15,
            sensor_timestamps={
                "gas_level": 100.0,
                "temperature": 100.0,
                "distance": 100.0,
            },
            timestamp=100.0,
            sequence=1,
        )

        self.assertTrue(validate_sensor_packet(packet))

    def test_non_dictionary_rejected(self):
        self.assertFalse(validate_sensor_packet(None))
        self.assertFalse(validate_sensor_packet([]))
        self.assertFalse(validate_sensor_packet("invalid"))

    def test_missing_sensors_rejected(self):
        packet = create_sensor_packet()
        del packet["sensors"]

        self.assertFalse(validate_sensor_packet(packet))

    def test_non_numeric_sensor_value_rejected(self):
        packet = create_sensor_packet(gas_level="high")

        self.assertFalse(validate_sensor_packet(packet))

    def test_boolean_sensor_value_rejected(self):
        packet = create_sensor_packet(temperature=True)

        self.assertFalse(validate_sensor_packet(packet))

    def test_non_finite_sensor_value_rejected(self):
        packet = create_sensor_packet(distance=float("nan"))

        self.assertFalse(validate_sensor_packet(packet))

    def test_invalid_sensor_timestamp_rejected(self):
        packet = create_sensor_packet(
            gas_level=450,
            sensor_timestamps={"gas_level": "invalid"},
        )

        self.assertFalse(validate_sensor_packet(packet))

    def test_unknown_sensor_name_rejected(self):
        packet = create_sensor_packet()
        packet["sensors"]["humidity"] = 60

        self.assertFalse(validate_sensor_packet(packet))


if __name__ == "__main__":
    unittest.main()