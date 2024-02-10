from time import sleep
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff

class Instant:
  t = None # Initialized in constructor
  def __init__(self, t = None):
    # Python has a fun little gotcha where default arguments are constructed only once, then copied
    self.t = ticks_ms() if t is None else t
  
  def millis(self): return self.t
  def seconds(self): return self.t/1000
  def __str__(self): return "<Instant @ {:.3f} seconds>".format(self.seconds())
  def __float__(self): return self.millis()
  def __int__(self): return self.millis()
  
  def __add__(self, other): return Instant(ticks_add(int(self), int(other)))
  # Subtract from this instant -- Determines an interval
  def __sub__(self, other): return ticks_diff(int(self), int(other))
  
  def __gt__(self, other): return self.__sub__(other) > 0
  def __lt__(self, other): return self.__sub__(other) < 0
  def __eq__(self, other): return int(self) == int(other)
  def __ge__(self, other): return self.__eq__(other) or self.__gt__(other)
  def __le__(self, other): return self.__eq__(other) or self.__lt__(other)
  
  def sleep_until(self): sleep(max(0, self - Instant())/1000)
