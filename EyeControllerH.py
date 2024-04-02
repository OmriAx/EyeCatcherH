from servo_controller import ServoController
import asyncio
import busio
from board import SCL, SDA

class EyeDataController:
    def __init__(self, debug=False):
        self.eyeData = {
            'cam_x': 512.0,
            'cam_y': 512.0,
            'eye_x': 512.0,
            'eye_y': 512.0,
            'blink': 0.0,
            'mouth': 0.0,
        }
        self.ConfigData = {
            'auto_blink': 1.0,
            'cam_x_p': 0.0,
            'cam_x_i': 0.0,
            'cam_x_d': 0.0,
            'cam_y_p': 0.0,
            'cam_y_i': 0.0,
            'cam_y_d': 0.0,
            'eye_x_p': 0.0,
            'eye_x_i': 0.0,
            'eye_x_d': 0.0,
            'eye_y_p': 0.0,
            'eye_y_i': 0.0,
            'eye_y_d': 0.0,
            'eye_open': 0.5,
            'servo_0_min': 270.0,
            'servo_0_max': 390.0,
            'servo_1_min': 280.0,
            'servo_1_max': 400.0,
            'servo_2_min': 270.0,
            'servo_2_max': 390.0,
            'servo_3_min': 280.0,
            'servo_3_max': 400.0,
            'servo_4_min': 280.0,
            'servo_4_max': 400.0,
            'servo_5_min': 280.0,
            'servo_5_max': 400.0,
            'servo_6_min': 250.0,
            'servo_6_max': 450.0,
            'servo_7_min': 320.0,
            'servo_7_max': 380.0,
        }
        self.debug = debug

        # Set the minimum and maximum angles for the servos
        self.min_angles = [self.ConfigData['servo_0_min'], self.ConfigData['servo_1_min'],
                           self.ConfigData['servo_2_min'], self.ConfigData['servo_3_min'],
                           self.ConfigData['servo_4_min'], self.ConfigData['servo_5_min'],
                           self.ConfigData['servo_6_min'], self.ConfigData['servo_7_min']]
        self.max_angles = [self.ConfigData['servo_0_max'], self.ConfigData['servo_1_max'],
                           self.ConfigData['servo_2_max'], self.ConfigData['servo_3_max'],
                           self.ConfigData['servo_4_max'], self.ConfigData['servo_5_max'],
                           self.ConfigData['servo_6_max'], self.ConfigData['servo_7_max']]

        # Create an instance of the ServoController
        i2c = busio.I2C(SCL, SDA)
        self.servo_controller = ServoController(i2c)

        # Set the minimum and maximum angles for each servo
        for i in range(8):
            self.servo_controller.set_min_angle(i, self.min_angles[i])
            self.servo_controller.set_max_angle(i, self.max_angles[i])

    async def run(self):
        await self.servo_controller.homing()

    def set_servo_angles(self, angles):
        # Set the absolute angles for the servos
        for i in range(len(angles)):
            self.servo_controller.set_absolute_angle(i, angles[i])

    def set_fractional_servo_angles(self, fractions):
        # Set the fractional angles for the servos
        for i in range(len(fractions)):
            self.servo_controller.set_fractional_angle(i, fractions[i])

    def set_servo_min_angle(self, servo_index, min_angle):
        # Set the minimum angle for a specific servo
        self.min_angles[servo_index] = min_angle
        self.servo_controller.set_min_angle(servo_index, min_angle)

    def set_servo_max_angle(self, servo_index, max_angle):
        # Set the maximum angle for a specific servo
        self.max_angles[servo_index] = max_angle
        self.servo_controller.set_max_angle(servo_index, max_angle)

    def close(self):
        self.loop.close()