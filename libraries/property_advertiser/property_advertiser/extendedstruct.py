import traceback
from .base import BaseProperty
from extendedstruct import *

class ExtendedStructProperty(BaseProperty,ExtendedStruct):
  update_callback = None
  def __init__(self, *fields): ExtendedStruct.__init__(self, *fields)
  def setValue(self, value):
    if not isinstance(value, dict): return False
    for k in self:
      if k in value: ExtendedStruct.__setitem__(self, k, value[k])
    
    try: self.update_callback()
    except: pass
    
    return True
  def getValue(self, update_callback):
    self.update_callback = update_callback
    return self
  def deserializeValue(self, msg):
    try: self.setBytes(msg)
    except Exception as e:
      print("WARN: Bad extended struct packet:", traceback.format_exception(e))
      return False
    return True
  def serializeValue(self): return self.getBytes()
  def __setitem__(self, i, v):
    ExtendedStruct.__setitem__(self, i, v)
    if not self.update_callback is None:
      try: self.update_callback()
      except: pass
  def __str__(self): return ExtendedStruct.__str__(self)

