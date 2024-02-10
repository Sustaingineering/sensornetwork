# Sustaingineering Sensor Network

What it is -- This is a monorepo repository for all devices within the Sustaingineering sensor network. Each device
communicates over a CAN bus to gather data from various areas over a large structure, such as a home or solar panel
grid. Individual code files for each device are designed to be very simple, and just advertise a series of "properties."
Hence, code files for devices are under "src/" and are named for each device. (TODO this doesn't exist yet)

Code files under "libraries" are support libraries that are common between multiple devices. This is where the bulk of
the code is (or will be). This includes git modules for 3rd party libraries.

A file called "build.sh" copies all of these files into individual build directories, which can then be placed directly
on the device in question with no additional work, and everything should *just work.*

TODO: The build process isn't implemented yet...
