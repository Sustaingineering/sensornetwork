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
    except e:
      print("WARN: Bad struct packet:", e)
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
  
  # See `addProperty` for usage
  def setPropEntry(self, prop_entry):
    # The map is done by CAN ID and name, both stored in the same map
    self.properties[prop_entry[0]] = prop_entry
    self.properties[prop_entry[1]] = prop_entry
  def updatePropStatus(self, prop_entry, status):
    self.setPropEntry((*prop_entry[:3], status))
  
  # Register a new property
  def addProperty(self, can_id, name, prop):
    if int(can_id) & 0x07FF != can_id:
      raise "Provided CAN ID is not a valid 11-bit CAN identifier. It might be too big"
    if not isinstance(name, str):
      raise "Provided name is not a string"
    if can_id in self.properties:
      raise "Provided CAN ID is already registered"
    if name in self.properties:
      raise "Provided name is already registered"
    if not isinstance(prop, BaseProperty):
      raise "Provided property is not an instance of BaseProperty"
    
    self.setPropEntry((can_id, name, prop, NoDataStatus()))
  
  def getPropEntry(self, name_or_can_id):
    if not name_or_can_id in self.properties:
      raise "Property " + str(name_or_can_id) + " not found"
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
    prop_entry[2].setValue(value) # Assign the value change
    self.flagLocalPropertyUpdate(prop_entry) # Record the update for sending
    self.updatePropStatus(prop_entry, LocalDataStatus())
  
  def __iter__(self):
    return filter(lambda s: isinstance(s, str), self.properties.keys())
  
  # Process an incoming packet
  def receive(self, can_id, msg):
    if not can_id in self.properties:
      print("WARN: Received packet with unknown ID 0x{:03X}".format(can_id))
      return False
    
    prop_entry = self.properties[can_id]
    if not prop_entry[2].deserializeValue(msg):
      print("WARN: Failed to decode packet with ID 0x{:03x}. Nothing updated".format(can_id))
      self.updatePropStatus(prop_entry, ErrorStatus())
      return False
    
    if isinstance(prop_entry[3], LocalDataStatus):
      print("WARN: Transitioning from local to remote data. Somebody is using a duplicate ID.")
    
    self.updatePropStatus(prop_entry, RemoteDataStatus(Instant() + self.data_timeout))
    self.property_expiry.append(prop_entry)
    return True
  
  # Transmit queued updates, remove expired remote properties, and process received messages in the queue
  def eventLoop(self):
    if not self.transmitter is None:
      while self.property_updates:
        prop = self.property_updates.pop()
        if not self.transmitter.send(prop[0], prop[2].serializeValue()):
          print("WARN: Failed to send updates for", prop[1])
    
    # Iterate over recent expiries, stop when there's nothing else to expire
    while len(self.property_expiry) and self.property_expiry[0][3].expiry() <= Instant():
      entry = self.property_expiry.pop(0)
      # Double check that nothing has changed since this entry: Get the newest version
      entry = self.properties[entry[0]]
      if not entry.expiry() is None and entry.expiry() <= Instant():
        self.updatePropStatus(entry, ExpiredStatus())
    
    # Process received packets
    if not self.receiver is None:
      while not (packet := self.receiver.receive()) is None:
        self.receive(packet[0], packet[1])
  
  def __str__(self):
    def formatProp(propname):
      prop = self.properties[propname]
      return '"{}" ({}) - {}'.format(propname, str(prop[3]), str(prop[2]))
    return '\n'.join(map(formatProp, self))
 
