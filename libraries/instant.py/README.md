# instant.py

> A simple library to measure changes in time with some nice syntax, which uses `adafruit_ticks` under the hood.

**BE AWARE that this library depends on adafruit_ticks, and so it will WRAP AROUND at 2^28 ms, or about 6 days.**

See the example below:
```py
from instant import Instant

# Create an Instant to capture a moment in time
a = Instant()
print(a)

# Add milliseconds to put the Instant into the future
b = a+2000
# Compute a delta in ms between Instants
print(a-b)

# Sleep until a particular instant (somewhat roughly)
b.sleep_until()

# We can also compare Instants to find out which is later
if a < Instant():
  print("Time works!")

# BE AWARE that this library depends on adafruit_ticks, and so it will WRAP AROUND at 2^28 ms, or about 6 days
```
