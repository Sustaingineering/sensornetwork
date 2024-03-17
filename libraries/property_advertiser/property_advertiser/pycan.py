import can
from .base import Transmitter, Receiver

class PycanTransmitter(Transmitter):
  def __init__(self, can): self.can = can
  def send(self, can_id, msg): return self.can.send(can.Message(arbitration_id=can_id, data=msg, is_extended_id=False))
class PycanReceiver(Receiver):
  def __init__(self, can, timeout=2.0):
    self.can = can
    self.timeout = timeout
  def deinit(self): pass
  
  # For use in `with` statements
  def __enter__(self): return self
  def __exit__(self, u1, u2, u3): pass
  
  def receive(self):
    msg = self.can.recv(self.timeout)
    return None if msg is None else (msg.arbitration_id, msg.data)

class CanBusInterface(PycanTransmitter, PycanReceiver):
  def __init__(self, *args, timeout=2.0, **kwargs):
    can_bus = can.Bus(*args, **kwargs)
    PycanTransmitter.__init__(self, can_bus)
    PycanReceiver.__init__(self, can_bus, timeout)
    

