# data_utils

> Helper classes for data aquisition and counting stuff.

## rate_counter

A simple frequency counter. Use this to turn a variable frequency interrupt into a frequency value. This is particularly
useful for anemometer counting.

Constructor: `RateCounter(self, base_rate=1, watchdog_timeout=1000*60*60*24)`:
 * `base_rate` - A value multiplier. What does 1 Hz correspond to? To use with the Sparkfun weather station anemometer,
 set this to 2.4 to get wind speeds in km/h since a tick frequency of 1 Hz corresponds to 2.4 km/h of wind.
 * `watchdog_timeout` -- The point at which the timer decides that an interval is effectively zero. This prevents a
 nonzero wind speed from being held for a long time when the wind is barely moving. Set this to a reasonable cutoff for
 zero wind. I'd recommend 10 seconds (10*1000) for the Sparkfun anemometer since this corresponds to 0.24 km/h wind.

Methods:
 * `tick()` - Call when an event is triggered to count the rate of this event. For example, a switch interrupt from an
 anemometer sensor.
 * `watchdog_tick()` - Run this periodically to trigger the watchdog that zeroes out the measured value when ticks
 aren't happening. Calling this a lot won't actually do anything -- This only sets the value to zero once the
 `RateCounter` has been inactive for a while.

Example:
```py
from time import sleep
from data_utils.rate_counter import RateCounter

rc = RateCounter()

rc.tick()
for i in range(1, 10):
  sleep(i)
  rc.tick()
  print("Tick at", rc.value, "Hz")
```
