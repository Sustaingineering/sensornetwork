# property_advertiser

> A library to sync a dictionary of pre-arranged properties between devices over a CAN bus or similar.

As opposed to protocols like SAE J1939, this protocol is designed to be very simple with as few bells and whistles as
possible. To use this library, start by defining some property types (such as integer, floating point, or other
specialized types) that can be serialized into 6 bytes. Next, assign properties on a `PropertyRegistry` by a CAN ID and
name to be used in code, along with one of the types you created earlier.

You now have the base registry, which needs to be created in *exactly the same way* (see the caveats below) on each
device in the network. From there, the registry can be created with a transmitter and/or receiver depending on which
protocol you want to use, and properties can be assigned as you would with a dictionary.

## The following caveats MUST be addressed in your usage:
* Each device MUST have the same properties stored in the registry, which are
each encoded in the exact same way. If the respective codebases are out of
sync, no or bad data will be received.
* ONLY ONE physical CAN transmitter may write to a particular property. If
more than one transmitter uses the same ID, the CAN IDs will collide and
cause data corruption. Make sure that each property is designed to be set in
only one place.
* Watch out for update frequency. When you call `eventLoop`, any properties
that have been updated will be sent over the bus. If there is no delay
between transmissions, the transmitter will flood the bus and no other device
will be able to get any other data through. Keep in mind, in the example
above, I have the data timeout set at 10 seconds. The data has to *arrive*
every ten seconds. It needs to be sent more frequently to account for delays,
but it does not need to be sent continously. Avoid overloading the bus by
delaying how often you reassign properties or run the event loop.

## Example
See `example.py`.
