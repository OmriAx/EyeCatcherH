# test_servo_controller.py
import asyncio
from ControllerH import ServoController
from board import SCL, SDA
import busio

async def test_servo_movement():
    i2c = busio.I2C(SCL, SDA)
    controller = ServoController(i2c)

    print("Testing individual servo movement...")
    for servo_index in range(8):
        print(f"Moving servo {servo_index}...")
        controller.set_absolute_angle(servo_index, 0)
        await controller.move_servo(servo_index)
        await asyncio.sleep(1)
        controller.set_absolute_angle(servo_index, 90)
        await controller.move_servo(servo_index)
        await asyncio.sleep(1)
        controller.set_absolute_angle(servo_index, 180)
        await controller.move_servo(servo_index)
        await asyncio.sleep(1)

    print("Testing simultaneous servo movement...")
    for angle in range(0, 181, 45):
        print(f"Moving all servos to angle {angle}...")
        for servo_index in range(8):
            controller.set_absolute_angle(servo_index, angle)
        await controller.run()
        await asyncio.sleep(2)

    print("Testing fractional angle movement...")
    fractions = [0.0, 0.25, 0.5, 0.75, 1.0]
    for fraction in fractions:
        print(f"Moving all servos to fractional angle {fraction}...")
        for servo_index in range(8):
            controller.set_fractional_angle(servo_index, fraction)
        await controller.run()
        await asyncio.sleep(2)

    print("Testing min and max angle limits...")
    for servo_index in range(8):
        print(f"Testing servo {servo_index} limits...")
        controller.set_min_angle(servo_index, 30)
        controller.set_max_angle(servo_index, 150)
        controller.set_absolute_angle(servo_index, 0)
        await controller.move_servo(servo_index)
        await asyncio.sleep(1)
        controller.set_absolute_angle(servo_index, 180)
        await controller.move_servo(servo_index)
        await asyncio.sleep(1)

    print("Testing complex movement patterns...")
    for _ in range(3):
        for servo_index in range(8):
            controller.set_absolute_angle(servo_index, 0)
        await controller.run()
        await asyncio.sleep(1)
        for servo_index in range(8):
            controller.set_absolute_angle(servo_index, 90)
        await controller.run()
        await asyncio.sleep(1)
        for servo_index in range(8):
            controller.set_absolute_angle(servo_index, 180)
        await controller.run()
        await asyncio.sleep(1)

    print("Servo testing complete!")

async def test_homing():
    i2c = busio.I2C(SCL, SDA)
    controller = ServoController(i2c)

    print("Testing homing function...")
    await controller.homing()
    print("Homing test complete.")

async def test_smoothing_factors():
    i2c = busio.I2C(SCL, SDA)
    controller = ServoController(i2c)

    print("Testing different smoothing factors...")
    controller.set_smoothing_factor(0, 0.1)  # Slow and smooth movement for servo 0
    controller.set_smoothing_factor(1, 0.5)  # Moderate speed for servo 1
    controller.set_smoothing_factor(2, 0.9)  # Fast movement for servo 2
    # Set smoothing factors for other servos as desired

    for servo_index in range(8):
        controller.set_absolute_angle(servo_index, 0)
    await controller.run()
    await asyncio.sleep(2)

    for servo_index in range(8):
        controller.set_absolute_angle(servo_index, 180)
    await controller.run()
    await asyncio.sleep(2)

    print("Smoothing factor test complete.")

if __name__ == "__main__":
    asyncio.run(test_homing())
    asyncio.run(test_smoothing_factors())
    asyncio.run(test_servo_movement())