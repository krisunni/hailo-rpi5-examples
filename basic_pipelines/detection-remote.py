import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import hailo
from hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from detection_pipeline import GStreamerDetectionApp

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.new_variable = 42  # New variable example

    def new_function(self):  # New function example
        return "The meaning of life is: "

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Using the user_data to count the number of frames
    user_data.increment()
    string_to_print = f"\n"

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Parse the detections and log their information
    detection_count = 0
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()  # Get bounding box
        confidence = detection.get_confidence()
        string_to_print += (f"Detection Lablel: {label}")

        #if label == "person":  # Example of filtering for person detections
            #x_min, y_min, x_max, y_max = bbox.get_bbox_coords()  # Get bounding box coordinates
            #string_to_print += (f"Detection: {detection}")
        x1_norm = bbox.xmin()
        y1_norm = bbox.ymin()
        x2_norm = bbox.xmax()
        y2_norm = bbox.ymax()
        x1 = int(x1_norm * width)
        y1 = int(y1_norm * height)
        x2 = int(x2_norm * width)
        y2 = int(y2_norm * height)
        string_to_print += f"Detection {detection_count}:"
        string_to_print += f"Label = {label},"
        string_to_print += f"BBox = {(x1, y1, x2 - x1, y2 - y1)}"
        string_to_print += f"Confidence = {confidence:.2f}\n"
            
        detection_count += 1

    print(string_to_print)
    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
