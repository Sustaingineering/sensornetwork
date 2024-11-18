"""
`adafruit_ina228`
====================================================

CircuitPython driver for the INA228 current sensor.

Implementation Notes
--------------------

**Hardware:**

* `Adafruit INA228 20-bit High or Low Side Power Monitor - <https://www.adafruit.com/product/5832>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware (2.2.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

* Based on INA219 code: https://github.com/adafruit/Adafruit_CircuitPython_INA219/blob/3.4.24/adafruit_ina219.py 
"""

from micropython import const 
from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_register.i2c_bits import ROBits, RWBits


#__version__ = "0.0.0+auto.0"
#__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_INA219.git"

# Bits
# pylint: disable=too-few-public-methods

# The least signficant bit is 195.3125uV which is 0.0001953125 V
VBusLSB = 0.0001953125 #V
# At +-163.84mV, the least signficant bit is 312.5nV which is 0.0003125mV
VShuntLSB_163 = 0.0003125 #mV
# At +-40.96mV, the least significant bit is 78.125nV which is 0.000078125mV
VShuntLSB_40 = 0.000078125 #mV
# The least significant bit is 7.8125mC which is 0.0078125C
TempLSB = 0.0078125 #C

# CONFIGURATION REGISTER
_REG_CONFIG = const(0x00)

class ResetEC:
    #Constants for `RSTACC` - reset energy and charge

    EC_NORMAL = 0x00 # normal operation
    EC_RESET = 0x01 # clear regs to default

# ADC Delay is an 8bit reg that sets delay to 2ms times the 8bit number

class TempComp:
    #Constants for `TEMPCOMP` - enabling shunt temp compensation

    TempComp_Dis = 0x00 # disable temp comp
    TempComp_En = 0x01 # enable temp comp

class ADCrange:
    #Constants for`ADCRANGE` - range selection across IN+ and IN-

    ADCRange_163mV = 0x00 # set range to +-163.84mV
    ADCRange_40mV = 0x01 # set range to +- 40.96mV

# ADC CONFIGURATION REGISTER 
_REG_ADCCONFIG = const(0x01)

class Mode:
    #Constants for `MODE`

    SHUTDOWN1 = 0x00 # Shutdown
    VBUS_TRIG = 0x01 # Triggered bus voltage, single shot
    VSHUNT_TRIG = 0x02 # Triggered shunt voltage, single shot
    VBUS_VSHUNT_TRIG = 0x03 # Triggered shunt voltage and bus voltage, single shot
    TEMP_TRIG = 0x04 # Triggered temperature, single shot
    TEMP_VBUS_TRIG = 0x05 # Triggered temperature and bus voltage, single shot
    TEMP_VSHUNT_TRIG = 0x06 # Triggered temperature and shunt voltage, single shot
    TEMP_VBUS_VSHUNT_TRIG = 0x07 # Triggered bus voltage, shunt voltage and temperature, single shot
    SHUTDOWN2 = 0x08 # Shutdown
    VBUS_CONST = 0x09 # Continuous bus voltage only
    VSHUNT_CONST = 0x0A # Continuous shunt voltage only
    VBUS_VSHUNT_CONST = 0x0B # Continuous shunt and bus voltage
    TEMP_CONST = 0x0C # Continuous temperature only
    TEMP_VBUS_CONST = 0x0D # Continuous bus voltage and temperature
    TEMP_VSHUNT_CONST = 0x0E # Continuous temperature and shunt voltage
    TEMP_VBUS_VSHUNT_CONST = 0x0F # Continuous bus voltage, shunt voltage and temperature

class VBusTime:
    #Constants for `VBUSCT` - bus voltage conversion time

    VBUS_T_50us = 0x00 # set conversion time to 50us
    VBUS_T_84us = 0x01 # set conversion time to 84us
    VBUS_T_150us = 0x02 # set conversion time to 150us
    VBUS_T_280us = 0x03 # set conversion time to 280us
    VBUS_T_540us = 0x04 # set conversion time to 540us
    VBUS_T_1052us = 0x05 # set conversion time to 1052us
    VBUS_T_2074us = 0x06 # set conversion time to 2074us
    VBUS_T_4120us = 0x07 # set conversion time to 4120us

class VShuntTime:
    #Constants for `VSHCT` - shunt voltage conversion time

    VSHUNT_T_50us = 0x00 # set conversion time to 50us
    VSHUNT_T_84us = 0x01 # set conversion time to 84us
    VSHUNT_T_150us = 0x02 # set conversion time to 150us
    VSHUNT_T_280us = 0x03 # set conversion time to 280us
    VSHUNT_T_540us = 0x04 # set conversion time to 540us
    VSHUNT_T_1052us = 0x05 # set conversion time to 1052us
    VSHUNT_T_2074us = 0x06 # set conversion time to 2074us
    VSHUNT_T_4120us = 0x07 # set conversion time to 4120us

class TempTime:
    #Constants for `VTCT` - temperature conversion time

    TEMP_T_50us = 0x00 # set conversion time to 50us
    TEMP_T_84us = 0x01 # set conversion time to 84us
    TEMP_T_150us = 0x02 # set conversion time to 150us
    TEMP_T_280us = 0x03 # set conversion time to 280us
    TEMP_T_540us = 0x04 # set conversion time to 540us
    TEMP_T_1052us = 0x05 # set conversion time to 1052us
    TEMP_T_2074us = 0x06 # set conversion time to 2074us
    TEMP_T_4120us = 0x07 # set conversion time to 4120us

class AvgCount:
    #Constants for 'AVG' - ADC sample averaging count

    AVGCNT_1 = 0x00 # set averaging count to 1
    AVGCNT_4 = 0x01 # set averaging count to 4
    AVGCNT_16 = 0x02 # set averaging count to 16
    AVGCNT_64 = 0x03 # set averaging count to 64
    AVGCNT_128 = 0x04 # set averaging count to 128
    AVGCNT_256 = 0x05 # set averaging count to 256
    AVGCNT_512 = 0x06 # set averaging count to 512
    AVGCNT_1024 = 0x07 # set averaging count to 1024

# SHUNT CALIBRATION REGISTER
_REG_SHUNTCAL = const(0x02)

# SHUNT TEMP COEFF REGISTER
_REG_SHUNTTEMPCO = const(0x03)

# SHUNT VOLTAGE REGISTER
_REG_VSHUNT = const(0x04)

# BUS VOLTAGE REGISTER
_REG_VBUS = const(0x05)

# TEMPERATURE MEASUREMENT REGISTER
_REG_DIETEMP = const(0x06)

# CURRENT RESULT REGISTER
_REG_CURRENT = const(0x07)

# POWER RESULT REGISTER
_REG_POWER = const(0x08)

# ENERGY RESULT REGISTER
_REG_ENERGY = const(0x09)

# CHARGE RESULT REGISTER
_REG_CHARGE = const(0x0A)

# FLAGS AND ALERTS REGISTER
_REG_DIAGALERT = const(0x0B)

# make classes here if using alerts

# SHUNT OVERVOLTAGE THRESHOLD REGISTER
_REG_SOLV = const(0x0C)

# SHUNT UNDERVOLTAGE THRESHOLD REGISTER
_REG_SULV = const(0x0D)

# BUS OVERVOLTAGE THRESHOLD REGISTER
_REG_BOLV = const(0x0E)

# BUS UNDERVOLTAGE THRESHOLD REGISTER
_REG_BULV = const(0x0F)

# TEMP OVERLIMIT THRESHOLD REGISTER
_REG_TEMPLIMIT = const(0x10)

# POWER OVERLIMIT THRESHOLD REGISTER
_REG_PWRLIMIT = const(0x11)

# MANUFACTURER ID REGISTER
_REG_MANUID = const(0x3E)

# DEVICE ID REGISTER
_REG_DEVICEID = const(0x3F)


def _to_signed(num: int) -> int:
    if num > 0x7FFF:
        num -= 0x10000
    return num


class INA228:
    """Driver for the INA228 current sensor"""

    # Basic API:

    # INA228( i2c_bus, addr)  Create instance of INA228 sensor
    #    :param i2c_bus          The I2C bus the INA228 is connected to
    #    :param addr (0x40)      Address of the INA228 on the bus (default 0x40)

    # shunt_voltage               RO : shunt voltage scaled to mVolts
    # bus_voltage                 RO : bus voltage (V- to GND) scaled to volts (==load voltage)
    # current                     RO : current through shunt, scaled to mA
    # power                       RO : power consumption of the load, scaled to Watt
    
    # set_calibration_163mV_1A(max_current)   Initialize chip for +-163.84mV and 1A
    # set_calibration_40mV_1A(max_current)   Initialize chip for +-40.96mV and 1A 
    # set_calibration_40mV_2A(max_current)   Initialize chip for +-40.96mV and 2A 


    def __init__(self, i2c_bus: I2C, addr: int = 0x40) -> None:
        self.i2c_device = I2CDevice(i2c_bus, addr)
        self.i2c_addr = addr

        # Set chip to known config values to start
        self._shunt_cal = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_40mV_2A()


    # config register break-up
    reset = RWBits(1, _REG_CONFIG, 15, 2, False)
    reset_ec = RWBits(1, _REG_CONFIG, 14, 2, False)
    adc_delay = RWBits(8, _REG_CONFIG, 6, 2, False)
    temp_comp = RWBits(1, _REG_CONFIG, 5, 2, False)
    adc_range = RWBits(1, _REG_CONFIG, 4, 2, False)

    # adc config register break-up
    mode = RWBits(4, _REG_ADCCONFIG, 12, 2, False)
    vbus_time = RWBits(3, _REG_ADCCONFIG, 9, 2, False)
    vshunt_time = RWBits(3, _REG_ADCCONFIG, 6, 2, False)
    temp_time = RWBits(3, _REG_ADCCONFIG, 3, 2, False)
    avg_count = RWBits(3, _REG_ADCCONFIG, 0, 2, False)

    # shunt calibration register (16 bits)
    _raw_shunt_cal = RWBits(15, _REG_SHUNTCAL, 0, 2, False)

    # shunt temp coefficient register (16 bits)
    shunt_temp_coeff = RWBits(14, _REG_SHUNTTEMPCO, 0, 2, False)

    # shunt voltage register (24 bits)
    raw_shunt_voltage = ROBits(20, _REG_VSHUNT, 4, 3, False, True)

    # bus voltage register (24 bits)
    raw_bus_voltage = ROBits(20, _REG_VBUS, 4, 3, False, True)

    # temperature register (16 bits)
    raw_temp = ROBits(16, _REG_DIETEMP, 0, 2, False, True)

    # current register (24 bits)
    raw_current = ROBits(20, _REG_CURRENT, 4, 3, False, True)

    # power register (24 bits)
    raw_power = ROBits(24, _REG_POWER, 0, 3, False, True)

    # energy register (40 bits)
    raw_energy = ROBits(40, _REG_ENERGY, 0, 5, False, True)

    # charge register (40 bits)
    raw_charge = ROBits(40, _REG_CHARGE, 0, 5, False, True)


    # break-up _REG_DIAGALERT here if using alerts

    # shunt over/undervoltage, bus under/overvoltage, temp/power overlimit, manu/device id
    
    @property
    def calibration(self) -> int:
        """Calibration register (cached value)"""
        return self._shunt_cal  # return cached value

    @calibration.setter
    def calibration(self, shunt_cal: int) -> None:
        self._shunt_cal = (
            shunt_cal  # value is cached for ``current`` and ``power`` properties
        )
        self._raw_shunt_cal = self._shunt_cal

    @property
    def shunt_voltage(self) -> float: #returning in mV
        """The shunt voltage (between V+ and V-) in Volts""" 

        if self.adc_range == ADCrange.ADCRange_163mV:
            return self.raw_shunt_voltage * VShuntLSB_163
        
        elif self.adc_range == ADCrange.ADCRange_40mV:
            return self.raw_shunt_voltage * VShuntLSB_40

    @property
    def bus_voltage(self) -> float:
        """The bus voltage (between V- and GND) in Volts"""

        return self.raw_bus_voltage * VBusLSB

    @property
    def temp(self) -> float:
        """The temperature in C"""

        return self.raw_temp * TempLSB

    @property
    def current(self) -> float:
        """The current through the shunt resistor in milliamps."""
        # Sometimes a sharp load will reset the INA228, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available -> always set a cal value
        self._raw_shunt_cal = self._shunt_cal
        
        return self.raw_current * self._current_lsb

    @property
    def power(self) -> float:
        """The power through the load in Watts."""
        # Sometimes a sharp load will reset the INA228, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available -> always set a cal value
        self._raw_shunt_cal = self._shunt_cal

        return self.raw_power * self._power_lsb
    
    @property
    def energy(self) -> float:
        """The energy from the load in Joules."""
        # Sometimes a sharp load will reset the INA228, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available -> always set a cal value
        self._raw_shunt_cal = self._shunt_cal

        return self.raw_energy * self._energy_lsb
    
    @property
    def charge(self) -> float:
        """The charge of the load in Coulombs."""
        # Sometimes a sharp load will reset the INA228, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available -> always set a cal value
        self._raw_shunt_cal = self._shunt_cal

        return self.raw_charge * self._current_lsb

    def set_calibration_163mV_1A(self) -> None:  # pylint: disable=invalid-name
        """ Configures the INA228 to be able to measure +-163.84mV and 1A of current."""

        # Calculations:

        # VBUS_MAX = 85V             
        # VSHUNT_MAX = 0.16384       (Assumes range +-163.84mV)
        # RSHUNT = .015              (Resistor value in ohms)

        # 1. Determine max expected current
        # MaxExpected_I = 1.0A

        # 2. Calculate current LSB
        # CurrentLSB = MaxExpected_I/2^19
        # CurrentLSB = 0.00000190734 (2uA per bit) 
        self._current_lsb = 0.002

        # 3. Compute the calibration register
        # Cal = 13107.2 * 10^6 * CurrentLSB * RSHUNT (x 4 if ADCRange = 1)
        # Cal = 393.216
        self._shunt_cal = 393

        # 4. Calculate the power LSB
        # PowerLSB = 3.2 * CurrentLSB
        # PowerLSB = 0.0000064 (6uW per bit)
        self._power_lsb = 0.0000064  

        # 5. Calculate the energy LSB
        # EnergyLSB = 16 * PowerLSB
        # Energy LSB = 0.0001024 (98uJ per bit)
        self._energy_lsb = 0.0001024

        # Calculate max vals? See reference code

        # Set Calibration register to 'Cal' calculated above
        self._raw_shunt_cal = self._shunt_cal

        # Set Config register to take into account the settings above
        self.reset_ec = ResetEC.EC_NORMAL
        self.adc_delay = 0x05 # chosen randomly
        self.temp_comp = TempComp.TempComp_Dis # not accounting for temp
        self.adc_range = ADCrange.ADCRange_163mV

        # Set adc config register to take into account the settings above
        self.mode = Mode.VBUS_VSHUNT_CONST # constant or triggered?
        self.vbus_time = VBusTime.VBUS_T_540us 
        self.vshunt_time = VShuntTime.VSHUNT_T_540us 
        self.temp_time = TempTime.TEMP_T_540us 
        self.avg_count = AvgCount.AVGCNT_16
        # 8.64ms sample time
 
        self.shunt_temp_coeff = 0x00


    def set_calibration_40mV_1A(self) -> None:  # pylint: disable=invalid-name
        """ Configures the INA228 to be able to measure +-40.96mV and 1A of current."""

        # Calculations

        # VBUS_MAX = 85V             
        # VSHUNT_MAX = 0.04096       (Assumes range +-40.96mV)
        # RSHUNT = .015              (Resistor value in ohms)

        # 1. Determine max expected current
        # MaxExpected_I = 1.0A

        # 2. Calculate current LSB
        # CurrentLSB = MaxExpected_I/2^19
        # CurrentLSB = 0.00000190734 (2uA per bit) 
        self._current_lsb = 0.002

        # 3. Compute the calibration register
        # Cal = 13107.2 * 10^6 * CurrentLSB * RSHUNT (x 4 if ADCRange = 1)
        # Cal = 393.216 (x 4 = 1572.864)
        self._shunt_cal = 1573

        # 4. Calculate the power LSB
        # PowerLSB = 3.2 * CurrentLSB
        # PowerLSB = 0.0000064 (6uW per bit)
        self._power_lsb = 0.0000064  

        # 5. Calculate the energy LSB
        # EnergyLSB = 16 * PowerLSB
        # Energy LSB = 0.0001024 (98uJ per bit)
        self._energy_lsb = 0.0001024

        # Calculate max vals? See reference code

        # Set Calibration register to 'Cal' calculated above
        self._raw_shunt_cal = self._shunt_cal

        # Set Config register to take into account the settings above
        self.reset_ec = ResetEC.EC_NORMAL
        self.adc_delay = 0x05 # chosen randomly
        self.temp_comp = TempComp.TempComp_Dis # not accounting for temp
        self.adc_range = ADCrange.ADCRange_40mV

        # Set adc config register to take into account the settings above
        self.mode = Mode.VBUS_VSHUNT_CONST # constant or triggered?
        self.vbus_time = VBusTime.VBUS_T_540us 
        self.vshunt_time = VShuntTime.VSHUNT_T_540us 
        self.temp_time = TempTime.TEMP_T_540us 
        self.avg_count = AvgCount.AVGCNT_16
        # 8.64ms sample time
 
        self.shunt_temp_coeff = 0x00

    def set_calibration_40mV_2A(self) -> None:  # pylint: disable=invalid-name
        """ Configures the INA228 to be able to measure +-40.96mV and 2A of current."""

        # Calculations

        # VBUS_MAX = 85V             
        # VSHUNT_MAX = 0.04096       (Assumes range +-40.96mV)
        # RSHUNT = .015              (Resistor value in ohms)

        # 1. Determine max expected current
        # MaxExpected_I = 2.0A

        # 2. Calculate current LSB
        # CurrentLSB = MaxExpected_I/2^19
        # CurrentLSB = 0.00000381469 (4uA per bit) 
        self._current_lsb = 0.004

        # 3. Compute the calibration register
        # Cal = 13107.2 * 10^6 * CurrentLSB * RSHUNT (x 4 if ADCRange = 1)
        # Cal = 786.432 (x 4 = 3145.728)
        self._shunt_cal = 3146

        # 4. Calculate the power LSB
        # PowerLSB = 3.2 * CurrentLSB
        # PowerLSB = 0.0000128 (12uW per bit)
        self._power_lsb = 0.0000128  

        # 5. Calculate the energy LSB
        # EnergyLSB = 16 * PowerLSB
        # Energy LSB = 0.0002048 (205uJ per bit)
        self._energy_lsb = 0.0002049

        # Calculate max vals? See reference code

        # Set Calibration register to 'Cal' calculated above
        self._raw_shunt_cal = self._shunt_cal

        # Set Config register to take into account the settings above
        self.reset_ec = ResetEC.EC_NORMAL
        self.adc_delay = 0x05 # chosen randomly
        self.temp_comp = TempComp.TempComp_Dis # not accounting for temp
        self.adc_range = ADCrange.ADCRange_40mV

        # Set adc config register to take into account the settings above
        self.mode = Mode.VBUS_VSHUNT_CONST # constant or triggered?
        self.vbus_time = VBusTime.VBUS_T_540us 
        self.vshunt_time = VShuntTime.VSHUNT_T_540us 
        self.temp_time = TempTime.TEMP_T_540us 
        self.avg_count = AvgCount.AVGCNT_16
        # 8.64ms sample time
 
        self.shunt_temp_coeff = 0x00
