from servo_controller import ServoController
import asyncio
import time
import busio
from board import SCL, SDA

async def main():
    # Create an instance of the ServoController
    i2c = busio.I2C(SCL, SDA)
    servo_controller = ServoController(i2c)

    # Set the minimum and maximum angles for each servo
    min_angles = [0, 0, 0, 0, 0, 0, 0, 0]
    max_angles = [180, 180, 180, 180, 180, 180, 180, 180]
    for i in range(8):
        servo_controller.set_min_angle(i, min_angles[i])
        servo_controller.set_max_angle(i, max_angles[i])

    # Set initial angles for some servos
    servo_controller.set_absolute_angle(0, 90)  # Set servo 0 to 90 degrees
    servo_controller.set_fractional_angle(1, 0.25)  # Set servo 1 to 25% of its range

    # Start the servo controller
    asyncio.create_task(servo_controller.run())

    # Continuously update target angles in a loop
    while True:
        # Change the target angle for servo 0
        servo_controller.set_absolute_angle(0, 150)  # Set servo 0 to 150 degrees
        await asyncio.sleep(3)

        # Change the target angle for servo 1
        servo_controller.set_fractional_angle(1, 0.75)  # Set servo 1 to 75% of its range
        await asyncio.sleep(3)

        # Here we can add the wait for a reading from the AI

        # Add more target angle updates as needed

if __name__ == "__main__":
    asyncio.run(main())