from instant import Instant

class RateCounter:
  value = 0
  last_tick = None
  base_rate = None # Initialized in constructor
  watchdog_timeout = None # Initialized in constructor
  
  def __init__(self, base_rate=1, watchdog_timeout=1000*60*60*24):
    self.base_rate = base_rate
    self.watchdog_timeout = watchdog_timeout
  
  def tick(self):
    now = Instant()
    
    freq = 0
    if not self.last_tick is None:
      delta = now - self.last_tick
      freq = 1000.0 / delta
    
    self.last_tick = now
    
    self.value = freq * self.base_rate
    return self.value
  
  # Call this periodically to keep this counter safe from overflowing accidentally when there aren't enough
  # interrupts to trigger. Set the watchdog_timeout accordingly if intervals in days are important...
  def watchdog_tick(self):
    if not self.last_tick is None and (Instant() - self.last_tick) > self.watchdog_timeout:
      self.last_tick = None
      self.value = 0
    
