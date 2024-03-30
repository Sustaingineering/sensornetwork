import can
import serial_can2
from sustaingineering_defs import SUSTAINGINEERING_TRANSMIT_IVAL, SustaingineeringPropertyRegistry
import thingspeak_bulk_update
import os
from instant import Instant
import schedule
from datetime import datetime, timezone

# Thingspeak can only accept updates every 15s at max
thingspeak_update_ival = 15

def passfunc(): pass

# Set up thingspeak interface
api_key = os.environ.get('THINGSPEAK_KEY', None)
ch_id = os.environ.get('THINGSPEAK_CH_ID', None)

ch = thingspeak_bulk_update.Channel(id = ch_id, api_key = api_key)

# NOTE: Highly WIP!
# You need to also run `pip3 install python-can` wherever you're running this
# Also sometimes it randomly crashes if it receives bad serial data

bus = serial_can2.SerialBus(channel='/dev/ttyACM0')

# TODO: Move the below into the sustaingineering_defs file (once the Py interface has stabilized)
"""
  Run a receive loop to update properties. After setup, just call this with your loop function and it will run whenever
  there's an update, or every SUSTAINGINEERING_TRANSMIT_IVAL milliseconds.
"""
def runPycanReceiveLoop(loop, setup = passfunc):
  from property_advertiser.pycan import PycanReceiver
  iface = PycanReceiver(can=bus, timeout = 1.0) # Time out after 1s of waiting; Keep the scheduler ticking
  pr = SustaingineeringPropertyRegistry(transmitter = iface, receiver = iface)
  setup(pr)
  while True:
    loop(pr)
    pr.eventLoop()

def doUpdate(registry):
  update_base = { "created_at" : str(datetime.now(timezone.utc)), "status": "UNKNOWN" }
  if not registry["weatherstation_status"] is None:
    update_base["status"] = "ONLINE({}) v{:d}{}".format(
      str(registry["weatherstation_status"]["reset_reason"]) + (", FIRST" if registry["weatherstation_status"]["is_first_message"] else ""),
      int(registry["weatherstation_status"]["proto_version"]),
      "" if registry["weatherstation_status"]["release_build"] else "DEV"
    )
    
  if not registry["weatherstation_ambient"] is None:
    update_base["field1"] = registry["weatherstation_ambient"]["temperature"]
    update_base["field2"] = registry["weatherstation_ambient"]["humidity"]
    update_base["field3"] = registry["weatherstation_ambient"]["pressure"]

  print(update_base)
  #ch.bulk_update(data = { "updates": [update_base] })

def setup(registry):
  schedule.every(thingspeak_update_ival).seconds.do(doUpdate, registry=registry)

def loop(registry): schedule.run_pending()

runPycanReceiveLoop(loop, setup)
