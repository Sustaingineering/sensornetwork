import math

"""Base class for all bitfields"""
class BitField:
  """Name of property"""
  name = None
  """Returns the desired bit width"""
  def getBitWidth(self): return 0
  """Deserialize a raw bytearray"""
  def deserialize(self, data): return None
  """Serialize a value and return a bytearray"""
  def serialize(self, val): return bytearray()

"""A bitfield that encodes a Boolean value"""
class BoolField:
  """
  Arguments:
    name - The name of the bitfield
  """
  def __init__(self, name): self.name = name
  def getBitWidth(self): return 1
  def deserialize(self, data): return True if data[0] & 0x1 else False
  def serialize(self, val): return bytearray([0x1 if val else 0x0])

"""
  A bitfield that encodes a value as an integer. Depending on how you set the scale, you don't actually have to
  assign an integer to this field: An appropriate scale could allow for decimals to be sent.
"""
class IntField:
  """
  Arguments:
    name - The name of the bitfield
    bitwidth - The total width of the field in bits. Sign is included in this
    base - The zero point for this field. This is the zero point when the value is encoded
    scale - The step size of the integer to send. This is the minimum step that can be resolved.
    signed - Whether the value is signed. If True, this field will support values less than `base` as well.
  """
  def __init__(self, name, bitwidth, base = 0.0, scale = 1.0, signed = False):
    self.name = name
    self.bitwidth = bitwidth
    self.base = base
    self.scale = scale
    self.signed = signed
  def getBitWidth(self): return self.bitwidth
  def serialize(self, val):
    if not (isinstance(val, int) or isinstance(val, float)): raise ValueError("Invalid type of numeric field")
    
    unsigned_bitwidth = self.bitwidth - (1 if self.signed else 0)
    
    val = int((val - self.base) / self.scale)
    sign = val < 0
    val = abs(val)
    if val >> unsigned_bitwidth: raise OverflowError("Bitfield overflow")
    if sign:
      val = ~val
      val ^= (val >> unsigned_bitwidth) << unsigned_bitwidth
      val |= 1 << unsigned_bitwidth
      val += 1
    
    buf = bytearray(math.ceil(self.bitwidth / 8))
    i = 0
    while val:
      buf[i] = val & 0xFF
      val = val >> 8
      i += 1
    return buf
  def deserialize(self, data):
    if len(data) != math.ceil(self.bitwidth/8): raise RuntimeError("Wrong data length passed to deserialize")
    unsigned_bitwidth = self.bitwidth - (1 if self.signed else 0)
    
    val = 0
    i = len(data)
    while i > 0:
      i -= 1
      val = (val << 8) | data[i]
    
    sign = self.signed if (val >> unsigned_bitwidth) & 0x1 else False
    if sign: val = ~val
    val ^= (val >> unsigned_bitwidth) << unsigned_bitwidth
    if sign: val = -val - 1
    
    val = (self.base + float(val)*self.scale)
    return val

"""Bit shift an entire byte array left. This is like number << bits, but for a bytearray."""
def bitShiftBytearrayLeft(ba, bits):
  bytes = math.floor(bits / 8)
  bits = bits % 8
  if bytes:
    ba[bytes:] = ba[:-bytes]
    ba[0:bytes] = [0] * bytes
  
  carryover = 0
  for i in range(bytes, len(ba)):
    cn = ba[i] >> (8 - bits)
    ba[i] = carryover | ((ba[i] << bits) & 0xFF)
    carryover = cn
"""Bit shift an entire byte array right. This is like number >> bits, but for a bytearray."""
def bitShiftBytearrayRight(ba, bits):
  bytes = math.floor(bits / 8)
  bits = bits % 8
  if bytes:
    ba[0:len(ba)-bytes] = ba[bytes:]
    ba[len(ba)-bytes:] = [0] * bytes
  
  carryover = 0
  for i in reversed(range(0, len(ba) - bytes)):
    cn = ba[i] & (0xFF >> (8 - bits))
    ba[i] = ba[i] >> bits | (carryover << (8 - bits))
    carryover = cn
"""Create a mask bytearray. This is `bitlen` ones offset by `start`."""
def bitmaskByteArray(bitlen, start = 0):
  length = bitlen + start
  bytelength = math.ceil(length/8)
  buf = bytearray(bytelength)
  
  bits_remaining = bitlen
  i = 0
  while bits_remaining >= 8:
    buf[i] = 0xFF
    i += 1
    bits_remaining -= 8
    
  if bits_remaining: buf[i] = 0xFF >> (8 - bits_remaining)
  bitShiftBytearrayLeft(buf, start)
  
  return buf

"""
  A C bitfield-like struct that stores data directly in a bytearray. Set up your bitfields, then simply assign them by
  name like a normal dictionary.
"""
class ExtendedStruct:
  # Python has a little trick where member variables like this are initialized once
  # If they weren't initialized manually in the constructor, the dict would end up getting shared between every instance
  field_name_mappings = None
  bit_length = 0
  buf = None
  
  """
  Arguments
    *fields - Simply pass all bitfields you would like to add in order as arguments
  """
  def __init__(self, *fields):
    if self.field_name_mappings is None: self.field_name_mappings = {}
    
    for field in fields:
      if field.name in self.field_name_mappings: raise AttributeError("Duplicate prop name " + str(field.name))
      bitwidth = field.getBitWidth()
      sl = slice(self.bit_length, self.bit_length + bitwidth)
      self.bit_length += bitwidth
      self.field_name_mappings[field.name] = (sl, field)
    
    self.buf = bytearray(math.ceil(self.bit_length/8))
  
  def __setitem__(self, i, v):
    if isinstance(i, int):
      if i < 0 or i >= self.bit_length: raise IndexError("Bit outside of struct")
      
      if v: self.buf[math.floor(i/8)] |= (1 << (i%8))
      else: self.buf[math.floor(i/8)] &= (1 << (i%8)) ^ 0xFF
    elif isinstance(i, slice):
      start = max(i.start, 0)
      stop = min(i.stop, self.bit_length)
      start_byte = math.floor(start/8)
      length = stop - start
      start_offset = start % 8
      
      mask = bitmaskByteArray(length, start_offset)
      data = bytearray(len(mask))
      
      if isinstance(v, int):
        i = 0
        while not v == 0 and i < len(data):
          data[i] = v & 0xFF
          v = v >> 8
          i += 1
      elif isinstance(v, bytearray):
        data[0:min(len(v), len(data))] = v[0:min(len(v), len(data))]
      else: raise ValueError("Invalid value assignment to bitfield")
      
      bitShiftBytearrayLeft(data, start_offset)
      
      for i in range(0, len(data)):
        self.buf[start_byte + i] &= mask[i] ^ 0xFF
        self.buf[start_byte + i] |= data[i] & mask[i]
    else:
      if not i in self.field_name_mappings: raise KeyError("Field name not in struct")
      (sl, field) = self.field_name_mappings[i] # Lookup the field object and corresponding slice
      self[sl] = field.serialize(v) # Now set the corresponding slice to the field object's encoded version
  
  def __getitem__(self, i):
    if isinstance(i, int):
      if i < 0 or i >= self.bit_length: raise IndexError("Bit outside of struct")
      return (self.buf[math.floor(i/8)] >> (i%8)) & 0x1
    elif isinstance(i, slice):
      start = max(i.start, 0)
      stop = min(i.stop, self.bit_length)
      start_byte = math.floor(start/8)
      length = stop - start
      byte_length = math.ceil(length/8)
      start_offset = start % 8
      stop_offset = 8 - (stop % 8)
      
      data = self.buf[start_byte:start_byte+byte_length]
      if not stop_offset == 8: data[-1] &= 0xFF >> stop_offset
      bitShiftBytearrayRight(data, start_offset)
      
      return data
    else:
      if not i in self.field_name_mappings: raise KeyError("Field name not in struct")
      (sl, field) = self.field_name_mappings[i] # Lookup the field object and corresponding slice
      return field.deserialize(self[sl]) # Now return the field object's interpretation of these bits
  
  def getByteArray(self): return self.buf
  def getBitLength(self): return self.bit_length
  def getByteLength(self): return math.ceil(self.bit_length / 8)
  
  def __str__(self):
    s = "ExtendedStruct[" + " ".join(map(hex, self.buf)) + "\n"
    s += "".join([("  " + str(k) + " = " + str(self[k]) + "\n") for k in self.field_name_mappings.keys()])
    s += "]"
    return s

if __name__ == "__main__":
  ba1 = bytearray([0x12, 0x34, 0x00, 0x00])
  ba = bytearray(ba1)
  bitShiftBytearrayLeft(ba, 8)
  bitShiftBytearrayRight(ba, 8)
  assert(ba1 == ba)
  bitShiftBytearrayLeft(ba, 14)
  bitShiftBytearrayRight(ba, 6)
  bitShiftBytearrayRight(ba, 8)
  assert(ba1 == ba)
  
  s = ExtendedStruct(
    BoolField("1a"),
    BoolField("1b"),
    BoolField("1c"),
    BoolField("1d"),
    BoolField("1e"),
    BoolField("1f"),
    BoolField("1g"),
    BoolField("1h"),
    
    BoolField("2a"),
    BoolField("2b"),
    BoolField("2c"),
    BoolField("2d"),
    BoolField("2e"),
    BoolField("2f"),
    BoolField("2g"),
    BoolField("2h"),
  )
  
  s[0:7] = 0xFFFF
  assert(s.buf == bytearray([0x7F, 0x00]))
  assert(s[0:7] == bytearray([0x7F]))
  assert(s[4:8] == bytearray([0x7]))
  
  s[0:16] = 0xFFFF
  assert(s.buf == bytearray([0xFF, 0xFF]))
  assert(s[0:7] == bytearray([0x7F]))
  assert(s[4:8] == bytearray([0xF]))
  assert(s[0:16] == bytearray([0xFF,0xFF]))
  assert(s[8:16] == bytearray([0xFF]))
  
  s[0:7] = 0x0
  assert(s.buf == bytearray([0x80, 0xFF]))
  
  s[8:15] = 0x0
  assert(s.buf == bytearray([0x80, 0x80]))
  
  s[0:4] = 0x1
  s[4:8] = 0x2
  s[8:12] = 0x3
  s[12:16] = 0x4
  assert(s.buf == bytearray([0x21, 0x43]))
  assert(s[0:4] == bytearray([0x1]))
  assert(s[4:8] == bytearray([0x2]))
  assert(s[8:12] == bytearray([0x3]))
  assert(s[12:16] == bytearray([0x4]))
  assert(s[8:9] == bytearray([0x1]))
  assert(s[13:14] == bytearray([0x0]))
  assert(s[13:15] == bytearray([0x2]))
  
  s[0:16] = 0x0
  s["1a"] = True
  assert(s[0:8] == bytearray([0x1]))
  s["1h"] = True
  assert(s[0:8] == bytearray([0x81]))
  print(s)
  
  s = ExtendedStruct(
    IntField("a", 8),
    IntField("b", 8, signed = True),
    IntField("c", 8, base = -0.1, scale=0.1),
  )
  s["a"] = 255
  s["b"] = -1
  assert(s[0:16] == bytearray([0xFF, 0xFF]))
  assert(s["a"] == 255)
  assert(s["b"] == -1)
  
  s["c"] = 0.0
  assert(s.buf[2] == 0x1)
  assert(s["c"] == 0.0)
  
  s["c"] = 0.1
  assert(s.buf[2] == 0x2)
  assert(s["c"] == 0.1)
  print(s)
  
  #s["a"] = 256 # <- Overflow!
  #s["b"] = 128 # <- Overflow!

