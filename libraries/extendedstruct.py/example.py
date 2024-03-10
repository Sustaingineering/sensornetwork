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
print(s.getBytes())

# Bitfields also error on overflow:
s["a"] = 256 # <- Overflow!
