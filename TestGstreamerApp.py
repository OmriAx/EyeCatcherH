import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gst
from servo_controller import ServoController
from eye_data_controller import EyeDataController
import asyncio
import busio
from board import SCL, SDA
import threading
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time

# Try to import hailo python module
try:
    import hailo
except ImportError:
    exit("Failed to import hailo python module. Make sure you are in hailo virtual environment.")
from hailo_common_funcs import get_numpy_from_buffer, disable_qos

# -----------------------------------------------------------------------------------------------
# User defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# a sample class to be used in the callback function alowwing to count the number of frames
class app_callback_class:
    def __init__(self):
        self.frame_count = 0
        self.use_frame = False
        self.frame_queue = multiprocessing.Queue(maxsize=3)
        self.running = True

    def increment(self):
        self.frame_count += 1

    def get_count(self):
        return self.frame_count 

    def set_frame(self, frame):
        if not self.frame_queue.full():
            self.frame_queue.put(frame)

        
    def get_frame(self):
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        else:
            return None

# Create an instance of the class
user_data = app_callback_class()

# -----------------------------------------------------------------------------------------------
# User defined callback function
# -----------------------------------------------------------------------------------------------

# This is the callback function that will be called when data is available from the pipeline

def app_callback(pad, info, user_data):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK
        
    # using the user_data to count the number of frames
    user_data.increment()
    string_to_print = f"Frame count: {user_data.get_count()}\n"
    
    caps = pad.get_current_caps()
    if caps:
        # We can now extract information from the caps
        structure = caps.get_structure(0)
        if structure:
            # Extracting some common properties
            format = structure.get_value('format')
            width = structure.get_value('width')
            height = structure.get_value('height')
            # string_to_print += (f"Frame format: {format}, width: {width}, height: {height}\n")
                    
    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if user_data.use_frame:
        # get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)
    
    # get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    
    # parse the detections
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        if label == "person":
            string_to_print += (f"Detection: {label} {confidence:.2f}\n")
    
    if user_data.use_frame:
        # Note: using imshow will not work here, as the callback function is not running in the main thread
    	# Convert the frame to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    print(string_to_print)
    return Gst.PadProbeReturn.OK
    # Additional option is Gst.PadProbeReturn.DROP to drop the buffer not passing in to the rest of the pipeline
    # See more options in Gstreamer documentation

# This function is used to display the user data frame
def display_user_data_frame(user_data):
    while user_data.running:
        frame = user_data.get_frame()
        if frame is not None:
            cv2.imshow("User Frame", frame)
            cv2.waitKey(1)
        time.sleep(0.02)
    
# Default parameters

network_width = 640
network_height = 640
network_format = "RGB"
video_sink = "xvimagesink"
batch_size = 1

# If TAPPAS version is 3.26.0 or higher, use the following parameters:
nms_score_threshold=0.3 
nms_iou_threshold=0.45
thresholds_str=f"nms-score-threshold={nms_score_threshold} nms-iou-threshold={nms_iou_threshold} output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
# else (TAPPAS version is 3.25.0)
# thresholds_str=""

def parse_arguments():
    parser = argparse.ArgumentParser(description="Detection App")
    parser.add_argument("--input", "-i", type=str, default="/dev/video0", help="Input source. Can be a file, USB or RPi camera (CSI camera module). \
                        For RPi camera use '-i rpi'. \
                        Defaults to /dev/video0")
    parser.add_argument("--use-frame", "-u", action="store_true", help="Use frame from the callback function")
    parser.add_argument("--show-fps", "-f", action="store_true", help="Print FPS on sink")
    parser.add_argument("--disable-sync", action="store_true", help="Disables display sink sync, will run as fast possible.")
    parser.add_argument("--dump-dot", action="store_true", help="Dump the pipeline graph to a dot file pipeline.dot")
    return parser.parse_args()

def QUEUE(name, max_size_buffers=3, max_size_bytes=0, max_size_time=0):
    return f"queue name={name} max-size-buffers={max_size_buffers} max-size-bytes={max_size_bytes} max-size-time={max_size_time} ! "

def get_source_type(input_source):
    # This function will return the source type based on the input source
    # return values can be "file", "mipi" or "usb"
    if input_source.startswith("/dev/video"):
        # check if the device is available

        return 'usb'
    else:
        if input_source.startswith("rpi"):
            return 'rpi'
        else:
            return 'file'
  

class GStreamerApp(Gtk.Window):
    def __init__(self, args):
        Gtk.Window.__init__(self, title="Hailo Detection App")
        self.set_default_size(800, 600)
        self.set_border_width(10)
        self.set_icon_from_file("path/to/icon.png")

        # Create an instance of the ServoController or EyeDataController
        i2c = busio.I2C(SCL, SDA)
        self.servo_controller = ServoController(i2c)
        # or
        # self.eye_data_controller = EyeDataController()

        # Create a vertical box to hold the widgets
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Create a menu bar
        menu_bar = Gtk.MenuBar()
        
        # Create menu items
        file_menu = Gtk.MenuItem(label="File")
        help_menu = Gtk.MenuItem(label="Help")
        
        # Create submenus
        file_submenu = Gtk.Menu()
        file_menu.set_submenu(file_submenu)
        
        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self.on_open_clicked)
        file_submenu.append(open_item)
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit_clicked)
        file_submenu.append(quit_item)
        
        help_submenu = Gtk.Menu()
        help_menu.set_submenu(help_submenu)
        
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.on_about_clicked)
        help_submenu.append(about_item)
        
        # Add menu items to the menu bar
        menu_bar.append(file_menu)
        menu_bar.append(help_menu)
        
        # Add the menu bar to the app
        vbox.pack_start(menu_bar, False, False, 0)

        # Create a toolbar
        toolbar = Gtk.Toolbar()
        
        # Create toolbar buttons
        start_button = Gtk.ToolButton(Gtk.STOCK_MEDIA_PLAY)
        start_button.set_tooltip_text("Start Detection")
        start_button.connect("clicked", self.on_start_button_clicked)
        toolbar.insert(start_button, -1)
        
        stop_button = Gtk.ToolButton(Gtk.STOCK_MEDIA_STOP)
        stop_button.set_tooltip_text("Stop Detection")
        stop_button.connect("clicked", self.on_stop_button_clicked)
        toolbar.insert(stop_button, -1)
        
        # Add the toolbar to the app
        vbox.pack_start(toolbar, False, False, 0)

        # Create a button to choose the HEF file
        hef_button = Gtk.Button(label="Choose HEF File")
        hef_button.connect("clicked", self.on_hef_button_clicked)
        vbox.pack_start(hef_button, False, False, 0)

        # Create a label to display the selected HEF file path
        self.hef_label = Gtk.Label(label="No HEF file selected")
        vbox.pack_start(self.hef_label, False, False, 0)

        # Create a status bar
        self.status_bar = Gtk.Statusbar()
        
        # Add the status bar to the app
        vbox.pack_end(self.status_bar, False, False, 0)

        # Set the process title
        setproctitle.setproctitle("Hailo Detection App")
        
        # Initialize variables
        tappas_workspace = os.environ.get('TAPPAS_WORKSPACE', '')
        if tappas_workspace == '':
            print("TAPPAS_WORKSPACE environment variable is not set. Please set it to the path of the TAPPAS workspace.")
            exit(1)
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.postprocess_dir = os.path.join(tappas_workspace, 'apps/h8/gstreamer/libs/post_processes')
        self.default_postprocess_so = os.path.join(self.postprocess_dir, 'libyolo_hailortpp_post.so')
        self.default_network_name = "yolov5"
        self.video_source = self.options_menu.input
        self.source_type = get_source_type(self.video_source)
        self.hef_path = None
        
        # Set user data parameters
        user_data.use_frame = self.options_menu.use_frame

        if (self.options_menu.disable_sync):
            self.sync = "false" 
        else:
            self.sync = "true"
        
        if (self.options_menu.dump_dot):
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = self.current_path
        
        # Initialize GStreamer        
        Gst.init(None)
        
        # Create a GStreamer pipeline 
        self.pipeline = self.create_pipeline()
        
        # connect to hailo_display fps-measurements
        if (self.options_menu.show_fps):
            print("Showing FPS")
            self.pipeline.get_by_name("hailo_display").connect("fps-measurements", self.on_fps_measurement)

        # Create a GLib Main Loop
        self.loop = GLib.MainLoop()

    def on_hef_button_clicked(self, button):
        # Create a file chooser dialog to select the HEF file
        dialog = Gtk.FileChooserDialog(
            title="Select HEF File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        # Add a filter to show only HEF files
        hef_filter = Gtk.FileFilter()
        hef_filter.set_name("HEF Files")
        hef_filter.add_pattern("*.hef")
        dialog.add_filter(hef_filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.hef_path = dialog.get_filename()
            self.hef_label.set_label(self.hef_path)
        dialog.destroy()

    def on_start_button_clicked(self, button):
        if self.hef_path is None:
            self.update_status("Please select a HEF file first.")
            return

        # Set the HEF path in the options menu
        self.options_menu.hef_path = self.hef_path

        # Create a new thread to run the detection pipeline
        detection_thread = threading.Thread(target=self.run_detection)
        detection_thread.daemon = True
        detection_thread.start()

    def on_stop_button_clicked(self, button):
        # Stop the detection pipeline
        self.pipeline.set_state(Gst.State.NULL)
        
        # Reset the servo positions
        asyncio.run(self.servo_controller.homing())

    def on_open_clicked(self, menu_item):
        # Handle the "Open" menu item click
        pass

    def on_quit_clicked(self, menu_item):
        # Stop the detection pipeline
        self.pipeline.set_state(Gst.State.NULL)
        
        # Reset the servo positions
        asyncio.run(self.servo_controller.homing())
        
        # Quit the app
        Gtk.main_quit()

    def on_about_clicked(self, menu_item):
        # Create and show an about dialog
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("Hailo Detection App")
        about_dialog.set_version("1.0")
        about_dialog.set_comments("An app for object detection using Hailo accelerators")
        about_dialog.set_website("https://hailo.ai")
        about_dialog.run()
        about_dialog.destroy()

    def run_detection(self):
        # Move the servos to their default positions
        asyncio.run(self.servo_controller.homing())

        # Run the detection pipeline
        self.run()

    def update_status(self, message):
        context_id = self.status_bar.get_context_id("status")
        self.status_bar.push(context_id, message)
        
    def on_fps_measurement(self, sink, fps, droprate, avgfps):
        print(f"FPS: {fps:.2f}, Droprate: {droprate:.2f}, Avg FPS: {avgfps:.2f}")
        return True

    def create_pipeline(self):
        pipeline_string = self.get_pipeline_string()
        try:
            pipeline = Gst.parse_launch(pipeline_string)
        except Exception as e:
            print(e)
            print(pipeline_string)
            exit(1)
        return pipeline
    
    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            loop.quit()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            loop.quit()
        return True
    
    def get_pipeline_string(self):
        if (self.source_type == "rpi"):
            source_element = f"libcamerasrc name=src_0 auto-focus-mode=2 ! "
            source_element += f"video/x-raw, format={network_format}, width=1536, height=864 ! "
            source_element += QUEUE("queue_src_scale")
            source_element += f"videoscale ! "
            source_element += f"video/x-raw, format={network_format}, width={network_width}, height={network_height}, framerate=30/1 ! "
        
        elif (self.source_type == "usb"):
            source_element = f"v4l2src device={self.video_source} name=src_0 ! "
            source_element += f"video/x-raw, width=640, height=480, framerate=30/1 ! "
        else:  
            source_element = f"filesrc location={self.video_source} name=src_0 ! "
            source_element += QUEUE("queue_dec264")
            source_element += f" qtdemux ! h264parse ! avdec_h264 max-threads=2 ! "
            source_element += f" video/x-raw,format=I420 ! "
        source_element += QUEUE("queue_scale")
        source_element += f" videoscale n-threads=2 ! "
        source_element += QUEUE("queue_src_convert")
        source_element += f" videoconvert n-threads=3 name=src_convert ! "
        source_element += f"video/x-raw, format={network_format}, width={network_width}, height={network_height}, pixel-aspect-ratio=1/1 ! "
        
        
        pipeline_string = "hailomuxer name=hmux "
        pipeline_string += source_element
        pipeline_string += "tee name=t ! "
        pipeline_string += QUEUE("bypass_queue", max_size_buffers=20) + "hmux.sink_0 "
        pipeline_string += "t. ! " + QUEUE("queue_hailonet")
        pipeline_string += "videoconvert n-threads=3 ! "
        pipeline_string += f"hailonet hef-path={self.hef_path} batch-size={batch_size} {thresholds_str} ! "
        pipeline_string += QUEUE("queue_hailofilter")
        pipeline_string += f"hailofilter function-name={self.default_network_name} so-path={self.default_postprocess_so} qos=false ! "
        pipeline_string += QUEUE("queue_hmuc") + " hmux.sink_1 "
        pipeline_string += "hmux. ! " + QUEUE("queue_hailo_python")
        pipeline_string += QUEUE("queue_user_callback")
        pipeline_string += f"identity name=identity_callback ! "
        pipeline_string += QUEUE("queue_hailooverlay")
        pipeline_string += f"hailooverlay ! "
        pipeline_string += QUEUE("queue_videoconvert")
        pipeline_string += f"videoconvert n-threads=3 ! "
        pipeline_string += QUEUE("queue_hailo_display")
        pipeline_string += f"fpsdisplaysink video-sink={video_sink} name=hailo_display sync={self.sync} text-overlay={self.options_menu.show_fps} signal-fps-measurements=true "
        print(pipeline_string)
        return pipeline_string
    
    def dump_dot_file(self):
        print("Dumping dot file...")
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
        return False
    
    def run(self):
        # Add a watch for messages on the pipeline's bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        # Connect pad probe to the identity element
        identity = self.pipeline.get_by_name("identity_callback")
        identity_pad = identity.get_static_pad("src")
        identity_pad.add_probe(Gst.PadProbeType.BUFFER, app_callback, user_data)
        
        # get xvimagesink element and disable qos
        # xvimagesink is instantiated by fpsdisplaysink
        hailo_display = self.pipeline.get_by_name("hailo_display")
        xvimagesink = hailo_display.get_by_name("xvimagesink0")
        xvimagesink.set_property("qos", False)
        
        # Disable QoS to prevent frame drops
        disable_qos(self.pipeline)

        
        # Set Timed callback to display user data frame
        if (self.options_menu.use_frame):
            GLib.timeout_add_seconds(0.03, display_user_data_frame, user_data)

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)
        
        # dump dot file
        if (self.options_menu.dump_dot):
            GLib.timeout_add_seconds(3, self.dump_dot_file)
        
        # Run the GLib event loop
        try:
            self.loop.run()
        except:
            pass

        # Clean up
        self.pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    args = parse_arguments()
    app = GStreamerApp(args)
    app.show_all()
    Gtk.main()