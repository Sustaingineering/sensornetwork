# serial-can2.py
> Based on KB1RD's fork of the serial_can file in the python-can library. Adds support for 11-bit IDs to the CAN serial
interface. Source is LGPL-3.0 licensed.

**Note that licensing for this code may be different from the rest of the project!!!**

See https://github.com/KB1RD/python-can/blob/05a66643e694f6cf01a7139f0eafc3aef30a2101/doc/interfaces/serial.rst for docs

This library is only needed when:
1. Until https://github.com/hardbyte/python-can/pull/1758 merges into a release (if it merges)
2. And when using a Feather as a gateway to test the CAN bus with the Pi codebase running on your computer.

