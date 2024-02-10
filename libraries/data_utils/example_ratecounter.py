from time import sleep
from data_utils.rate_counter import RateCounter

rc = RateCounter()

rc.tick()
for i in range(1, 10):
  sleep(i)
  rc.tick()
  print("Tick at", rc.value, "Hz")
