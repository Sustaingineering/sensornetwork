import sys
import struct
from instant import Instant

# A base class for all property types
class BaseProperty:
  def __init__(self): pass
  
  def setValue(self, value): return False
  def getValue(self, update_callback): return None
  
  def deserializeValue(self, msg): return True
  def serializeValue(self): return bytearray()
  
  def __str__(self): return "BaseProperty: No data"

# A property that encodes data using the `struct` library
class StructProperty(BaseProperty):
  value = None
  def __init__(self, fmt): self.fmt = fmt
  def setValue(self, value):
    self.value = value
    return True
  def getValue(self, update_callback): return self.value
  def deserializeValue(self, msg):
    try:
      self.value = struct.unpack(self.fmt, msg)
      return True
    except:
      print("WARN: Bad struct packet:", sys.exc_info()[1])
      return False
  def serializeValue(self): return struct.pack(self.fmt, *self.value)
  def __str__(self): return "StructProperty: " + str(self.value)

# Base class for transmitters
class Transmitter:
  # Send a packet with an ID and a body (msg). Return True on success
  def send(self, can_id, msg): return False
# Base class for receivers
class Receiver:
  # Receive a packet. Return a tuple of (ID, body) if a packet is available, None otherwise
  def receive(self): return None

# A class that functions as a transmitter and receiver. When a packet is
# transmitted, it's added to a queue and passed to a receiver.
class DummyTransceiver(Transmitter, Receiver):
  buf = None
  def __init__(self): self.buf = set()
  def send(self, can_id, msg):
    print("MSG ID {:03x} - {}".format(can_id, msg))
    self.buf.add((can_id, msg))
    return True
  def receive(self):
    return self.buf.pop() if self.buf else None

class PropertyStatus: # Status of a particular property; See PropertyRegistry
  def isValid(self): return False
  def isLocal(self): return None
  def expiry(self): return None
  def __str__(self): return "UNKNOWN STATUS"
class NoDataStatus(PropertyStatus): # Nothing received or recorded
  def isValid(self): return False
  def isLocal(self): return True
  def expiry(self): return None
  def __str__(self): return "NO DATA"
class LocalDataStatus(PropertyStatus): # Data recorded locally
  def isValid(self): return True
  def isLocal(self): return True
  def expiry(self): return None
  def __str__(self): return "LOCAL"
class RemoteDataStatus(PropertyStatus): # Data received from remote
  def __init__(self, expiry_instant): self.expiry_instant = expiry_instant
  def isValid(self): return True
  def isLocal(self): return False
  def expiry(self): return self.expiry_instant
  def __str__(self): return "REMOTE"
class ExpiredStatus(PropertyStatus): # Data received from remote, but expired
  def isValid(self): return False
  def isLocal(self): return False
  def expiry(self): return None
  def __str__(self): return "REMOTE/EXPIRED"
class ErrorStatus(PropertyStatus): # Corrupt data received from remote
  def isValid(self): return False
  def isLocal(self): return False
  def expiry(self): return None
  def __str__(self): return "REMOTE/ERROR"

# A dictionary of registered property names and types
# Each property name is given a BaseProperty instance, which is used to track
# the values associated with each name, and encode them for sending.
class PropertyRegistry:
  transmitter = None # Defined in ctor
  receiver = None # Defined in ctor
  
  properties = None
  property_updates = None
  property_expiry = None
  data_timeout = None # Defined in ctor
  
  warn_count_unknown_id = 0
  warn_count_corrupt = 0
  warn_id_local_transition = None
  
  def __init__(
    self,
    data_timeout = 10000, # Interval after which data is considered expired
    transmitter = None,
    receiver = None
  ):
    self.transmitter = transmitter
    self.receiver = receiver
    self.data_timeout = data_timeout
    self.properties = {}
    self.property_updates = set()
    self.property_expiry = []
  
  def flushWarnings(self):
    warnings = {
      "count_unknown_id": self.warn_count_unknown_id,
      "count_corrupt": self.warn_count_corrupt,
      "id_local_transition": self.warn_id_local_transition
    }
    self.warn_count_unknown_id = 0
    self.warn_count_corrupt = 0
    self.warn_id_local_transition = None
    return warnings
  
  # See `addProperty` for usage
  def setPropEntry(self, prop_entry):
    # The map is done by CAN ID and name, both stored in the same map
    self.properties[prop_entry[0]] = prop_entry
    self.properties[prop_entry[1]] = prop_entry
  def updatePropStatus(self, prop_entry, status):
    if prop_entry in self.property_expiry: self.property_expiry.remove(prop_entry)
    prop_entry = (*prop_entry[:3], status)
    self.setPropEntry(prop_entry)
    return prop_entry
  
  # Register a new property
  def addProperty(self, can_id, name, prop):
    if int(can_id) & 0x07FF != can_id:
      raise Exception("Provided CAN ID is not a valid 11-bit CAN identifier. It might be too big")
    if not isinstance(name, str):
      raise Exception("Provided name is not a string")
    if can_id in self.properties:
      raise Exception("Provided CAN ID is already registered")
    if name in self.properties:
      raise Exception("Provided name is already registered")
    if not isinstance(prop, BaseProperty):
      raise Exception("Provided property is not an instance of BaseProperty")
    
    self.setPropEntry((can_id, name, prop, NoDataStatus()))
  
  def getPropEntry(self, name_or_can_id):
    if not name_or_can_id in self.properties:
      raise Exception("Property " + str(name_or_can_id) + " not found")
    return self.properties[name_or_can_id]
  
  # Marks a proprety as local and flag it for sending
  def flagLocalPropertyUpdate(self, prop_entry):
    self.property_updates.add(prop_entry)
    self.updatePropStatus(prop_entry, LocalDataStatus())
  
  def getStatus(self, name_or_can_id):
    if not name_or_can_id in self.properties: return None
    return self.properties[name_or_can_id][3]
  
  def __getitem__(self, name_or_can_id):
    prop_entry = self.getPropEntry(name_or_can_id)
    if prop_entry[3].isValid():
      return prop_entry[2].getValue(lambda: self.flagLocalPropertyUpdate(prop_entry))
    return None
  
  def __setitem__(self, name_or_can_id, value):
    prop_entry = self.getPropEntry(name_or_can_id)
    if prop_entry[2].setValue(value): # Assign the value change
      self.flagLocalPropertyUpdate(prop_entry) # Record the update for sending
      self.updatePropStatus(prop_entry, LocalDataStatus())
  
  def __iter__(self):
    return filter(lambda s: isinstance(s, str), self.properties.keys())
  
  # Process an incoming packet
  def receive(self, can_id, msg):
    if not can_id in self.properties:
      self.warn_count_unknown_id += 1
      print("WARN: Received packet with unknown ID 0x{:03X}".format(can_id))
      return False
    
    prop_entry = self.properties[can_id]
    def deserialize():
      try: return prop_entry[2].deserializeValue(msg)
      except:
        print("WARN: Exception in deserialize:", sys.exc_info()[1])
        return False
    if not deserialize():
      self.warn_count_corrupt += 1
      print("WARN: Failed to decode packet with ID 0x{:03x}".format(can_id))
      self.updatePropStatus(prop_entry, ErrorStatus())
      return False
    
    if isinstance(prop_entry[3], LocalDataStatus):
      self.warn_id_local_transition = prop_entry
      print("WARN: Transitioning from local to remote data. Somebody is using a duplicate ID.")
    
    prop_entry = self.updatePropStatus(
      prop_entry,
      RemoteDataStatus(Instant() + self.data_timeout)
    )
    self.property_expiry.append(prop_entry)
    return True
  
  # Transmit queued updates, remove expired remote properties, and process received messages in the queue
  def eventLoop(self):
    def send(prop):
      try: return self.transmitter.send(prop[0], prop[2].serializeValue())
      except:
        print("WARN: Exception in transmitter send:", sys.exc_info()[1])
        return False
    
    if not self.transmitter is None:
      while self.property_updates:
        prop = self.property_updates.pop()
        if not send(prop): print("WARN: Failed to send updates for", prop[1])
    
    # Iterate over recent expiries, stop when there's nothing else to expire
    while len(self.property_expiry) and self.property_expiry[0][3].expiry() <= Instant():
      entry = self.property_expiry.pop(0)
      # Double check that nothing has changed since this entry: Get the newest version
      entry = self.properties[entry[0]]
      if not entry[3].expiry() is None and entry[3].expiry() <= Instant():
        self.updatePropStatus(entry, ExpiredStatus())
    
    # Process received packets
    def receive():
      try: return self.receiver.receive()
      except:
        print("WARN: Exception in receiver receive:", sys.exc_info()[1])
        return True
    if not self.receiver is None:
      while not (packet := receive()) is None:
        try: self.receive(packet[0], packet[1])
        except:
          print(
            "WARN: Exception processing packet with ID 0x{:03X}".format(packet[0]),
            sys.exc_info()[1]
          )
  
  def __str__(self):
    def formatProp(propname):
      prop = self.properties[propname]
      return '"{}" ({}) - {}'.format(propname, str(prop[3]), str(prop[2]))
    return '\n'.join(map(formatProp, self))

if __name__ == "__main__":
  import traceback
  import time
  
  tests = {}
  failed_tests = set()
  
  def test(f):
    tests[f.__name__] = f
  
  @test
  def StructPropEncoding():
    prop = StructProperty(">B")
    prop.setValue((123,))
    assert(prop.getValue(lambda: None) == (123,))
    assert(prop.serializeValue() == bytearray([123]))
  @test
  def StructPropDecoding():
    prop = StructProperty(">B")
    prop.deserializeValue(bytearray([123]))
    assert(prop.getValue(lambda: None) == (123,))
  @test
  def AddPropertyDuplicateCanFails():
    pr = PropertyRegistry()
    pr.addProperty(0, "test", BaseProperty())
    try:
      pr.addProperty(0, "test2", BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyInvalidCanFails():
    try:
      PropertyRegistry().addProperty(0xFFFF, "test", BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyInvalidCanFails2():
    try:
      PropertyRegistry().addProperty("notanumber", "test", BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyDuplicateNameFails():
    pr = PropertyRegistry()
    pr.addProperty(0, "test", BaseProperty())
    try:
      pr.addProperty(1, "test", BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyInvalidNameFails():
    try:
      PropertyRegistry().addProperty(0, 123, BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyInvalidNameFails():
    try:
      PropertyRegistry().addProperty(0, 123, BaseProperty())
    except: pass
    else: assert(False)
  @test
  def AddPropertyInvalidFails():
    try:
      PropertyRegistry().addProperty(0, "test", {})
    except: pass
    else: assert(False)
  @test
  def PropertyDefaultsNoData():
    pr = PropertyRegistry()
    pr.addProperty(0, "test", BaseProperty())
    assert(isinstance(pr.getStatus(0), NoDataStatus))
  @test
  def PropertyAssignUpdatesStatus():
    pr = PropertyRegistry()
    pr.addProperty(0, "test", StructProperty(">B"))
    pr["test"] = 123
    assert(isinstance(pr.getStatus(0), LocalDataStatus))
    assert(pr.property_updates)
  @test
  def PropertyReceiveUpdatesStatus():
    pr = PropertyRegistry(data_timeout=100)
    pr.addProperty(0, "test", StructProperty(">B"))
    pr.receive(0, bytearray((123,)))
    assert(isinstance(pr.getStatus(0), RemoteDataStatus))
    assert(len(pr.property_expiry))
    
    time.sleep(0.1)
    pr.eventLoop()
    assert(isinstance(pr.getStatus(0), ExpiredStatus))
    assert(len(pr.property_expiry) == 0)
  @test
  def PropertyReceiveUnknown():
    pr = PropertyRegistry(data_timeout=100)
    pr.receive(0, bytearray((123,)))
    assert(pr.warn_count_unknown_id == 1)
  @test
  def PropertyReceiveCorrupt():
    pr = PropertyRegistry(data_timeout=100)
    pr.addProperty(0, "test", StructProperty(">B"))
    pr.receive(0, bytearray())
    assert(isinstance(pr.getStatus(0), ErrorStatus))
    assert(pr.warn_count_corrupt == 1)
  @test
  def PropertyReceiveTransitionLocal():
    pr = PropertyRegistry(data_timeout=100)
    pr.addProperty(0, "test", StructProperty(">B"))
    pr["test"] = 123
    pr.receive(0, bytearray((123,)))
    assert(isinstance(pr.getStatus(0), RemoteDataStatus))
    assert(not pr.warn_id_local_transition is None)
  
  for test in tests.keys():
    print("Test", test, "----------------")
    try:
      tests[test]()
      print("TEST PASSED")
    except:
      failed_tests.add(test)
      print("TEST FAILED", traceback.format_exc())
  
  print()
  print("All tests complete,", len(failed_tests), "failed")
  for test in failed_tests:
    print(test, "FAILED")

