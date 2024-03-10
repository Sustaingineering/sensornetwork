from board import SPI
from digitalio import DigitalInOut
from adafruit_mcp2515.canio import Message, RemoteTransmissionRequest
from adafruit_mcp2515 import MCP2515 as CAN
from .base import Transmitter, Receiver

class AdafruitCanTransmitter(Transmitter):
  def __init__(self, can): self.can = can
  def send(self, can_id, msg): return self.can.send(Message(id=can_id, data=msg, extended=False))
class AdafruitCanReceiver(Receiver):
  def __init__(self, can, timeout=2.0): self.listener = can.listen(timeout=timeout)
  def deinit(self): self.listener.deinit()
  
  # For use in `with` statements
  def __enter__(self): return self
  def __exit__(self, u1, u2, u3): self.deinit()
  
  def receive(self, can_id, msg):
    msg = listener.receive()
    return None if msg is None else (msg.id, msg.data)

class FeatherCanInterface(AdafruitCanTransmitter, AdafruitCanReceiver):
  def __init__(self, timeout=2.0):
    cs = DigitalInOut(board.CAN_CS)
    cs.switch_to_output()
    spi = SPI()
    can_bus = CAN(spi, cs, loopback=False, silent=False)
    AdafruitCanTransmitter.__init__(self, can_bus)
    AdafruitCanReceiver.__init__(self, can_bus, timeout)
    

