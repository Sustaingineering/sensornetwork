# Sustaingineering Sensor Network

What it is -- This is a monorepo repository for all devices within the Sustaingineering sensor network. Each device
communicates over a CAN bus to gather data from various areas over a large structure, such as a home or solar panel
grid. Individual code files for each device are designed to be very simple, and just advertise a series of "properties"
to be exchanged over a CAN bus.

## Navigating
Files to be placed on CircuitPython drives are "build" by a simple build system (in reality, just copied) that places
libraries, common code files, and device specific code files in the output directory for each device. This software is
all contained in `build.sh`. I haven't been able to find a viable alternative that meets our requirements, so this build
system has to be done in house I guess.

Files in the library folder are a mix of git submodules and libraries included directly into the source tree. A good
number of these are Adafruit libraries to interface with peripherals a bit more easily. The Sustaingineering-authored
libraries ideally shouldn't need much maintenance -- Code here *should* be much better tested and carefully written,
though whether we have the time is another story...

Anyway, the code you want to edit is *probably* in the `code_*.py` files in the root directory, or some of the code in
the `common` directory.

## Directory structure
* `libraries` -- support libraries that are common between multiple devices. This is where the bulk of the code is (or
  will be). This includes git modules for 3rd party libraries.
  * Each library is organized in its own subdirectory, which contains code, README files, and whatnot.
  * Code is placed in a subdirectory with the same name as the parent directory, or a single file also with the same
  name as the parent directory. This is done for compatibility with Adafruit's libraries.
* `common` -- Common files for every device. This just gets copied to the target directory.
* `code_NAME.py` -- The code file for a particular device. These code files define a new device build target, which
  causes `build.sh` to create the appropriate target directory in `build`.
* `build.sh` -- Takes all of the code and library files, and packages them into a single folder of files to be placed on
  the target device. This is compatible with CircuitPython, so it should *just work* if you plop all the files onto the
  chosen circuitpython drive. (**TODO:** Make a script that automatically uploads to CP with rsync or smth)
  * This should work for MacOS and Linux users
  * Windows users -- I don't know? You could always install Cygwin, or the Ubuntu compatibility thing...
  * Maybe I should rewrite in Python? Windows users, if this is an issue for you, please open an issue on GitHub and
  I'll address it. I just don't know how much this matters.
* `build` -- The output from `build.sh`
