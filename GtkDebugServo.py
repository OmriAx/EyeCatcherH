from servo_controller import ServoController
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import asyncio
import busio
from board import SCL, SDA

class TestApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="ServoController Test")
        self.set_default_size(400, 300)

        # Set the minimum and maximum angles for the servos
        self.min_angles = [0, 0, 0, 0, 0, 0, 0, 0]
        self.max_angles = [180, 180, 180, 180, 180, 180, 180, 180]

        # Create an instance of the ServoController
        i2c = busio.I2C(SCL, SDA)
        self.servo_controller = ServoController(i2c)

        # Set the minimum and maximum angles for each servo
        for i in range(8):
            self.servo_controller.set_min_angle(i, self.min_angles[i])
            self.servo_controller.set_max_angle(i, self.max_angles[i])

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        for i in range(8):
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            vbox.pack_start(hbox, True, True, 0)

            label = Gtk.Label(label=f"Servo {i}")
            hbox.pack_start(label, True, True, 0)

            angle_entry = Gtk.Entry()
            hbox.pack_start(angle_entry, True, True, 0)

            angle_button = Gtk.Button(label="Set Angle")
            angle_button.connect("clicked", self.on_angle_button_clicked, i, angle_entry)
            hbox.pack_start(angle_button, True, True, 0)

            fraction_entry = Gtk.Entry()
            hbox.pack_start(fraction_entry, True, True, 0)

            fraction_button = Gtk.Button(label="Set Fraction")
            fraction_button.connect("clicked", self.on_fraction_button_clicked, i, fraction_entry)
            hbox.pack_start(fraction_button, True, True, 0)

            min_entry = Gtk.Entry()
            hbox.pack_start(min_entry, True, True, 0)

            min_button = Gtk.Button(label="Set Min")
            min_button.connect("clicked", self.on_min_button_clicked, i, min_entry)
            hbox.pack_start(min_button, True, True, 0)

            max_entry = Gtk.Entry()
            hbox.pack_start(max_entry, True, True, 0)

            max_button = Gtk.Button(label="Set Max")
            max_button.connect("clicked", self.on_max_button_clicked, i, max_entry)
            hbox.pack_start(max_button, True, True, 0)

        self.connect("destroy", self.on_destroy)

    def on_angle_button_clicked(self, button, servo_index, entry):
        angle = float(entry.get_text())
        self.servo_controller.set_absolute_angle(servo_index, angle)

    def on_fraction_button_clicked(self, button, servo_index, entry):
        fraction = float(entry.get_text())
        self.servo_controller.set_fractional_angle(servo_index, fraction)

    def on_min_button_clicked(self, button, servo_index, entry):
        min_angle = float(entry.get_text())
        self.servo_controller.set_min_angle(servo_index, min_angle)

    def on_max_button_clicked(self, button, servo_index, entry):
        max_angle = float(entry.get_text())
        self.servo_controller.set_max_angle(servo_index, max_angle)

    async def run(self):
        await self.servo_controller.homing()

    def on_destroy(self, widget):
        asyncio.get_event_loop().stop()
        Gtk.main_quit()

async def main():
    win = TestApp()
    win.show_all()
    await win.run()
    Gtk.main()

if __name__ == "__main__":
    asyncio.run(main())