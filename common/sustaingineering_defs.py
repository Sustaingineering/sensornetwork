import time
from property_advertiser import PropertyRegistry, StructProperty, DummyTransceiver
from property_advertiser.extendedstruct import ExtendedStructProperty, BoolField, IntField, ReservedField, EnumField

# So, here's the thing: With a CAN bus, we can't just send JSON messages -- Each message has to fit in 6 bytes. That
# means we have to be efficient about things. That being said, it would be GREAT to just assign to things like they're
# a dictionary. That's why I wrote the property_advertiser library: With the property advertiser, you can just assign
# to your sensor's "properties" like they're a dictionary, and they will end up on the other devices. The PROBLEM with
# this is that each device has to be speaking the same language -- They need to know what the binary messages mean in
# order to populate the common, shared dictionary. Hence, the goal of the code below is to:

# 1. Provide some support code so we can use the same codebase on multiple devices
# 2. Define which IDs we want to use to communicate, software versions, time intervals, and other constants
# 3. Define the properties we want to use. We create a custom PropertyRegistry and add our desired properties to it
# 4. Finally, we define common "main" code for our devices that sets up the property registry and CAN bus

# -------------------------------------------------------------------------------------------------------------------- #

"""
  Enum values for the reset reason
  Keep track of the reset reason so we can detect abnormal events
  This is handled by the device status property, so it's set automatically!
"""
RESET_REASONS = [
  ("POWER_ON", 0),
  ("BROWNOUT", 1),
  ("SOFTWARE", 2),
  ("DEEP_SLEEP_ALARM", 3),
  ("RESET_PIN", 4),
  ("WATCHDOG", 5),
  ("RESCUE_DEBUG", 6),
  ("UNKNOWN", 7)
]
try:
  # https://docs.circuitpython.org/en/latest/shared-bindings/microcontroller/index.html#microcontroller.ResetReason
  import microcontroller
  def getResetReason(): return str(microcontroller.cpu.reset_reason)[28:]
except:
  def getResetReason(): return "POWER_ON" # TODO

# Increment every time breaking changes are made to the protocol below.
# Addition of properties should not need a change, but removal or change does.
PROTOCOL_VERSION = 0

SUSTAINGINEERING_TRANSMIT_IVAL = 2000 # How frequently data is transmitted
SUSTAINGINEERING_DATA_TIMEOUT = 10000 # How frequently data is cleared out if not received

# ID Allocations:
# ID allocations are arbitrary; This does not *need* to be done any particular way. However, for the sake of
# organization, I split the 11 bit address space into a 3 reserved bits, 4 bits for device ID, and 4 bits for field.
# The reserved bits of the ID are required to be ones. The bits are reserved in case we need to send different CAN
# messages on the same bus or something.
# The final device ID is reserved for status messages. The reason for this is because CAN IDs that are larger have a
# larger priority, so status messages will have the greatest priority.

# Device IDs
# These are assigned manually below on a per-feather basis, EXCEPT for the status ID. See the rationale above.
DEVICE_WEATHERSTATION = 0x0
DEVICE_STATUS         = 0xF # Special device code for device status messages

""" Determine the CAN ID from device ID and field ID """
def sid(dev_id, field_id): return (dev_id & 0xF) * 16 + (field_id & 0xF) + 0x0700

"""
  Define a common property type for status messages. Since this is a common data type used in EVERY device, I don't want
  to define it every time! This is the only common property at the moment, so it's the only one with its own definition.
"""
class StatusProperty(ExtendedStructProperty):
  def __init__(self): super().__init__(
    # Byte #1
    BoolField("release_build"), # Whether the running build is flagged as a release
    BoolField("is_first_message"), # Whether this is the first message sent after startup
    EnumField("reset_reason", 3, *RESET_REASONS), # Reason for a power reset; Used to detect errors
    ReservedField(3), # Reserved -- Make sure this always aligns to a byte
    
    # Byte #2
    # Protocol version (see PROTOCOL_VERSION). Wrap it around at 255; The specific value is not important, just the
    # difference between them in case of a version mismatch.
    IntField("proto_version", 8)
  )

"""Define a custom property registry for sustaingineering information"""
class SustaingineeringPropertyRegistry(PropertyRegistry):
  def __init__(self, transmitter = None, receiver = None):
    super().__init__(data_timeout = SUSTAINGINEERING_DATA_TIMEOUT, transmitter = transmitter, receiver = receiver)
    
    # Now, set up the properties
    self.addProperty(sid(DEVICE_STATUS, DEVICE_WEATHERSTATION), "weatherstation_status", StatusProperty())
    self.addProperty(sid(DEVICE_WEATHERSTATION, 0), "weatherstation_ambient", ExtendedStructProperty(
      IntField("temperature", 16, base = -200, scale = 0.01, signed = False), # -200C to 455.35C
      IntField("humidity", 8, base = 0, scale = 100.0/255.0, signed = False), # 0-100 (a percent)
      IntField("pressure", 16, base = 800.0, scale = 0.01, signed = False), # 800hPa - 1455.35 hPa
    ))
    self.addProperty(sid(DEVICE_WEATHERSTATION, 1), "weatherstation_windspeed", ExtendedStructProperty(
      IntField("10min", 12, base = 0, scale = 0.1, signed = False), # 0 to 409.6 km/hr
      IntField("gust", 12, base = 0, scale = 0.1, signed = False), # 0 to 409.6 km/hr
      IntField("instant", 12, base = 0, scale = 0.1, signed = False), # 0 to 409.6 km/hr
    )) 
    self.addProperty(sid(DEVICE_WEATHERSTATION, 2), "weatherstation_winddir", ExtendedStructProperty(
      IntField("10min", 12, base = 0, scale = 360.0/4096, signed = False), # 0 to 360 deg
      IntField("gust", 12, base = 0, scale = 360.0/4096, signed = False), # 0 to 360 deg
      IntField("instant", 12, base = 0, scale = 360.0/4096, signed = False), # 0 to 360 deg
    ))
    self.addProperty(sid(DEVICE_WEATHERSTATION, 3), "weatherstation_rain", ExtendedStructProperty(
      IntField("10min", 12, base = 0, scale = 0.1, signed = False), # 0 to 409.6 mm
      IntField("hourly", 12, base = 0, scale = 0.1, signed = False), # 0 to 409.6 mm
      IntField("boot", 4, base = 0, scale = 0.1, signed = False), # 0 to 1.6 mm
    ))
  
  first_msg = True # Set to true if this is the first message sent
  def assignStatusProperty(self, device_id):
    self[sid(DEVICE_STATUS, device_id)] = {
      "release_build": False, # TODO
      "is_first_message": self.first_msg,
      "reset_reason": getResetReason(),
      "proto_version": PROTOCOL_VERSION % 8,
    }
    self.first_msg = False

"""
  Run a transmit loop to send sensor values only. Calls the `sensor_refresh` loop provided. After setup, just run this
  function to put sensors on the bus without receiving anything.
"""
def runFeatherTransmitOnlyLoop(sensor_refresh):
  from property_advertiser.adafruitcan import FeatherCanInterface
  iface = FeatherCanInterface(timeout = float(SUSTAINGINEERING_TRANSMIT_IVAL)/1000.0)
  pr = SustaingineeringPropertyRegistry(transmitter = iface)
  while True:
    sensor_refresh(pr)
    pr.eventLoop()
    time.sleep(float(SUSTAINGINEERING_TRANSMIT_IVAL)/1000.0)

"""
  Run a transmit and receive loop to both advertise and update properties. After setup, just call this with your loop
  function and it will run whenever there's an update, or every SUSTAINGINEERING_TRANSMIT_IVAL milliseconds.
"""
def runFeatherTransceiveLoop(loop):
  from property_advertiser.adafruitcan import FeatherCanInterface
  iface = FeatherCanInterface(timeout = float(SUSTAINGINEERING_TRANSMIT_IVAL)/1000.0)
  pr = SustaingineeringPropertyRegistry(transmitter = iface, receiver = iface)
  while True:
    loop(pr)
    pr.eventLoop()

