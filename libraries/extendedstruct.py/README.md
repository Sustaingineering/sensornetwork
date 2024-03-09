# Extended Struct

> A C-like bitfield struct that supports assignment to a dictionary of typed fields.

This was written because the Python `struct` library...
1. Doesn't support [bitfields](https://en.wikipedia.org/wiki/Bit_field)
2. Doesn't support dictionary-like assignment (to make it similar to a C struct)

It's fairly intuitive to use, and the code base is well documented. See the example below:

## Example

```python
from extendedstruct import ExtendedStruct, IntField, BoolField

s = ExtendedStruct(
  # Store a simple unsigned integer (0-255)
  IntField("a", 8),
  # Store a signed integer (min -126, max 127)
  IntField("b", 8, signed = True),
  # Store an integer, but scale incoming numbers (min 0, max 25.5, in steps of 0.1)
  IntField("c", 8, base = -0.1, scale=0.1),
  # Store a single bit boolean
  BoolField("bool")
)

s["a"] = 255
s["b"] = -1
s["bool"] = True

# Behaves just like a normal dictionary
print(s["a"]) # Prints 255
print(s["b"]) # Prints -1
print(s["bool"]) # Prints True

# Even though the bitfield is an int bitfield, it can still store decimals thanks to the scale factor:
s["c"] = 0.0
print(s["c"]) # Prints 0.0

s["c"] = 0.11
print(s["c"]) # Prints 0.1 -- Note how the value is truncated to a step of 0.1

# Show the bitfield contents nicely
print(s)
# Print out the encoded struct
print(s.getByteArray())

# Bitfields also error on overflow:
s["a"] = 256 # <- Overflow!
```

Output:
```
255.0
-1.0
True
0.0
0.1
ExtendedStruct[0xff 0xff 0x2 0x1
  a = 255.0
  b = -1.0
  c = 0.1
  bool = True
]
bytearray(b'\xff\xff\x02\x01')
Traceback (most recent call last):
  File "example.py", line 32, in <module>
    s["a"] = 256 # <- Overflow!
  File ".../extendedstruct.py", line 190, in __setitem__
    self[sl] = field.serialize(v) # Now set the corresponding slice to the field object's encoded version
  File ".../extendedstruct.py", line 53, in serialize
    if val >> unsigned_bitwidth: raise OverflowError("Bitfield overflow")
OverflowError: Bitfield overflow
```
