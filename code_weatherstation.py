import board
from sustaingineering_defs import runFeatherTransmitOnlyLoop, DEVICE_WEATHERSTATION
import adafruit_sht4x
from adafruit_dps310.basic import DPS310

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

sht = adafruit_sht4x.SHT4x(i2c)
print("Found SHT4x with serial number", hex(sht.serial_number))
dps310 = DPS310(i2c)

sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
# Can also set the mode to enable heater
# sht.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
print("Current mode is: ", adafruit_sht4x.Mode.string[sht.mode])

def loop(registry):
  registry.assignStatusProperty(DEVICE_WEATHERSTATION)
  
  temperature, relative_humidity = sht.measurements
  registry["weatherstation_ambient"] = {
    "temperature": max(min(temperature, 455.35), -200),
    "humidity": max(min(relative_humidity, 100), 0),
    "pressure": max(min(dps310.pressure, 1455.35), 800),
  }

runFeatherTransmitOnlyLoop(loop)
