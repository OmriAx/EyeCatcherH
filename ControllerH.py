import asyncio
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

class ServoController:
    def __init__(self, i2c):
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50
        self.min_angles = [0] * 8
        self.max_angles = [180] * 8
        self.servo_counts = []
        self.current_angles = [0] * 8
        self.target_angles = [0] * 8
        self.smoothing_factors = [0.1] * 8  # Default smoothing factor of 0.1 for all servos
        self.update_servo_counts()

    def update_servo_counts(self):
        self.servo_counts = []
        for min_angle, max_angle in zip(self.min_angles, self.max_angles):
            self.servo_counts.append(self.angle_to_count(min_angle, max_angle))

    def angle_to_count(self, min_angle, max_angle):
        counts = []
        for angle in range(min_angle, max_angle + 1):
            count = int((angle / 180) * (2 ** 16 - 1))
            counts.append(count)
        return counts

    def set_min_angle(self, servo_index, angle):
        self.min_angles[servo_index] = angle
        self.update_servo_counts()

    def set_max_angle(self, servo_index, angle):
        self.max_angles[servo_index] = angle
        self.update_servo_counts()

    def set_absolute_angle(self, servo_index, angle):
        min_angle, max_angle = self.min_angles[servo_index], self.max_angles[servo_index]
        if angle < min_angle:
            angle = min_angle
        elif angle > max_angle:
            angle = max_angle
        self.target_angles[servo_index] = angle

    def set_fractional_angle(self, servo_index, fraction):
        min_angle, max_angle = self.min_angles[servo_index], self.max_angles[servo_index]
        angle = min_angle + (max_angle - min_angle) * fraction
        angle = int(round(angle))
        self.target_angles[servo_index] = angle

    def set_smoothing_factor(self, servo_index, smoothing_factor):
        self.smoothing_factors[servo_index] = smoothing_factor

    async def move_servo(self, servo_index, delay=0.01):
        servo_count = self.servo_counts[servo_index]
        min_angle, max_angle = self.min_angles[servo_index], self.max_angles[servo_index]
        current_angle = self.current_angles[servo_index]
        target_angle = self.target_angles[servo_index]
        smoothing_factor = self.smoothing_factors[servo_index]

        while abs(current_angle - target_angle) > 1:
            current_angle += (target_angle - current_angle) * smoothing_factor
            current_angle = int(round(current_angle))
            count = servo_count[current_angle - min_angle]
            self.pca.channels[servo_index].duty_cycle = count
            print(f"Moving servo {servo_index} to angle {current_angle}")
            self.current_angles[servo_index] = current_angle
            await asyncio.sleep(delay)

        # Set the servo to the final target angle
        count = servo_count[target_angle - min_angle]
        self.pca.channels[servo_index].duty_cycle = count
        print(f"Moving servo {servo_index} to angle {target_angle}")
        self.current_angles[servo_index] = target_angle

    async def run(self):
        tasks = [self.move_servo(i) for i in range(8)]
        await asyncio.gather(*tasks)

    async def homing(self):
        print("Homing all servos to 0.5 fractional angle...")
        for servo_index in range(8):
            self.set_fractional_angle(servo_index, 0.5)
        await self.run()
        print("Homing complete.")