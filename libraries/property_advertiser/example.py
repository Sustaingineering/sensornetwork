from property_advertiser import PropertyRegistry, StructProperty, DummyTransceiver

# We'll make a new type of Property that encodes a single float
# This will use the StructProperty as a base to encode the data
class FloatProperty(StructProperty):
  def __init__(self): super().__init__("!f")
  def getValue(self, update_callback): return self.value[0]
  def setValue(self, value):
    self.value = (value,)
    return True
  def __str__(self): return "NO DATA" if self.value is None else str(self.value[0])

# Create a subclass of the property registry with a custom property defined as
# a FloatProperty (this makes more sense when you read the code below).
class TestPropertyRegistry(PropertyRegistry):
  def __init__(self, data_timeout = 10000, transmitter = None, receiver = None):
    super().__init__(data_timeout = data_timeout, transmitter = transmitter, receiver = receiver)
    self.addProperty(0, "TEST", FloatProperty())

# Create a DummyTransceiver: Just sends messages from one registry to the other
# In a real implementation, this would be replaced with a CAN bus or similar
txn = DummyTransceiver()

# Registry #1. Imagine this registry code is running on a sensor node
reg1 = TestPropertyRegistry(transmitter = txn)
# Registry #2. Image this registry node is running on a different device
reg2 = TestPropertyRegistry(receiver = txn)

# Now, the DummyTransceiver acts like the imaginary CAN bus that connects
# registry 1 and registry 2

# Registries start out reporting no data for each property:
print("reg1:", reg1) # Prints: "TEST" (NO DATA) - NO DATA
# Property accesses are all also None:
print("reg1['TEST'] =", reg1["TEST"]) # Prints: None

print()

# Now, let's say we assign a property on registry 1...
reg1["TEST"] = 1.0

# Before doing anything else, registry 1 will reflect a local property, but
# registry 2 will still have no data for TEST.
print("reg1:", reg1)
print("reg2:", reg2)

# Now, run the event loops.
# In reality, these would be running continuously on each device.

# A good idea on a transmitter device would be to run this in a loop that
# assigns updates property values at a fixed interval lower than data_timeout.
# A good idea on a transceiver or receiver would be to set up the `Receiver` to
# wait for messages with a timeout, then simply update properties and call the
# eventLoop function in a while loop.

# Anyway, running them here transmits messages from reg1, then receives those
# messages from the DummyTransceiver on reg2
reg1.eventLoop()
reg2.eventLoop()
print()

# Now, you'll notice that the properties have updated
print("reg1:", reg1)
print("reg2:", reg2)

# Now, properties can be accessed like a dictionary
# So long as the event loop runs periodically enough, the dictionaries will
# *always* be synced between devices *1
print("reg1['TEST'] =", reg1["TEST"]) # Prints: 1.0
print("reg2['TEST'] =", reg2["TEST"]) # Prints: 1.0

# *1 - The following caveats MUST be addressed in your usage:
# * Each device MUST have the same properties stored in the registry, which are
# each encoded in the exact same way. If the respective codebases are out of
# sync, no or bad data will be received.
# * ONLY ONE physical CAN transmitter may write to a particular property. If
# more than one transmitter uses the same ID, the CAN IDs will collide and
# cause data corruption. Make sure that each property is designed to be set in
# only one place.
# * Watch out for update frequency. When you call `eventLoop`, any properties
# that have been updated will be sent over the bus. If there is no delay
# between transmissions, the transmitter will flood the bus and no other device
# will be able to get any other data through. Keep in mind, in the example
# above, I have the data timeout set at 10 seconds. The data has to *arrive*
# every ten seconds. It needs to be sent more frequently to account for delays,
# but it does not need to be sent continously. Avoid overloading the bus by
# delaying how often you reassign properties or run the event loop.

