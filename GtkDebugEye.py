import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from eye_data_controller import EyeDataController
import asyncio

class TestApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="EyeDataController Test")
        self.set_default_size(400, 300)
        self.eye_data_controller = EyeDataController()

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
        self.eye_data_controller.set_servo_angles([angle])

    def on_fraction_button_clicked(self, button, servo_index, entry):
        fraction = float(entry.get_text())
        self.eye_data_controller.set_fractional_servo_angles([fraction])

    def on_min_button_clicked(self, button, servo_index, entry):
        min_angle = float(entry.get_text())
        self.eye_data_controller.set_servo_min_angle(servo_index, min_angle)

    def on_max_button_clicked(self, button, servo_index, entry):
        max_angle = float(entry.get_text())
        self.eye_data_controller.set_servo_max_angle(servo_index, max_angle)

    def on_destroy(self, widget):
        self.eye_data_controller.close()
        Gtk.main_quit()

async def run_app():
    win = TestApp()
    win.show_all()
    await win.eye_data_controller.run()
    Gtk.main()

if __name__ == "__main__":
    asyncio.run(run_app())