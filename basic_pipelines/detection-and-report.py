import json
import gi
import paho.mqtt.client as mqtt
from gi.repository import Gst, GLib
import hailo
from hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from detection_pipeline import GStreamerDetectionApp
from datetime import datetime, timezone
# MQTT details
broker = "localhost"  # Replace with your broker address
port = 1883  # MQTT port
topic = "pi5/camera/1"
mqtt_client = mqtt.Client()
username = 'web'
password = 'web'
# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.new_variable = 42  # New variable example

    def new_function(self):  # New function example
        return "The meaning of life is: "

    def increment(self):  # Example increment method for counting frames
        self.new_variable += 1

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------
def app_callback(pad, info, user_data):
    # Open file for logging detections
    with open("detections_log.txt", "a") as log_file:
        # Get the GstBuffer from the probe info
        buffer = info.get_buffer()
        if buffer is None:
            return Gst.PadProbeReturn.OK

        user_data.increment()  # Frame counter increment
        string_to_print = "\n"

        # Get caps and format details
        format, width, height = get_caps_from_pad(pad)

        # Get detections from the buffer
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        # Parse detections and log/send information
        detection_data = []
        for detection_count, detection in enumerate(detections):
            label = detection.get_label()
            bbox = detection.get_bbox()
            confidence = detection.get_confidence()

            # Get bounding box coordinates in pixels
            x1 = int(bbox.xmin() * width)
            y1 = int(bbox.ymin() * height)
            x2 = int(bbox.xmax() * width)
            y2 = int(bbox.ymax() * height)

            # Log the detection details
            string_to_print += f"Detection {detection_count}: Label = {label}, BBox = {(x1, y1, x2 - x1, y2 - y1)}, Confidence = {confidence:.2f}\n"
            log_file.write(string_to_print)  # Write detection info to log file

            # Prepare detection data for MQTT message
            detection_data.append({
                "label": label,
                "bbox": {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1},
                "confidence": confidence,
                "utc": datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
            })

        # Publish detection data to MQTT topic
        mqtt_message = {
            "frame": user_data.new_variable,
            "detections": detection_data
        }
        # Attempt to publish and print an error if it fails
        result = mqtt_client.publish(topic, json.dumps(mqtt_message))
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Failed to publish message to {topic}: {mqtt.error_string(result.rc)}")

        # Print detection details to console
        print(string_to_print)

    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    mqtt_client.username_pw_set(username, password)
    # Connect to MQTT broker and stay connected for the session
    mqtt_client.connect(broker, port)
    try:
        app.run()
    finally:
        mqtt_client.disconnect()  # Ensure the client disconnects when the app ends
