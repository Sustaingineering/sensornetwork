import sys
from struct import pack
from board import SPI, CAN_CS
from digitalio import DigitalInOut
from adafruit_mcp2515.canio import Message, RemoteTransmissionRequest
from adafruit_mcp2515 import MCP2515 as CAN
from instant import Instant

# Take CAN messages, and send them over serial. To be used with the serial_can2 fork from python-can
# See https://python-can.readthedocs.io/en/stable/interfaces/serial.html

cs = DigitalInOut(CAN_CS)
cs.switch_to_output()

can_bus = CAN(SPI(), cs, loopback=False, silent=False)
listener = can_bus.listen(timeout=1.0)

start = Instant()
while True:
  msg = listener.receive()
  if msg is None: continue
  
  atr_id = msg.id + (0 if msg.extended else 0x20000000)
  header = pack("<BIBI", 0xAA, Instant()-start, len(msg.data), atr_id)
  
  sys.stdout.write(header + msg.data + bytearray([0xBB]))
