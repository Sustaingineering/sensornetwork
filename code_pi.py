import can
import serial_can2
from sustaingineering_defs import SUSTAINGINEERING_TRANSMIT_IVAL, SustaingineeringPropertyRegistry

# NOTE: Highly WIP!
# You need to also run `pip3 install python-can` wherever you're running this
# Also sometimes it randomly crashes if it receives bad serial data

bus = serial_can2.SerialBus(channel='/dev/ttyACM0')

# TODO: Move the below into the sustaingineering_defs file (once the Py interface has stabilized)
"""
  Run a receive loop to update properties. After setup, just call this with your loop function and it will run whenever
  there's an update, or every SUSTAINGINEERING_TRANSMIT_IVAL milliseconds.
"""
def runPycanReceiveLoop(loop):
  from property_advertiser.pycan import PycanReceiver
  iface = PycanReceiver(can=bus, timeout = float(SUSTAINGINEERING_TRANSMIT_IVAL)/1000.0)
  pr = SustaingineeringPropertyRegistry(transmitter = iface, receiver = iface)
  while True:
    loop(pr)
    pr.eventLoop()

# This is largely copied from 
def loop(registry):
  print()
  print()
  print(registry)

runPycanReceiveLoop(loop)
