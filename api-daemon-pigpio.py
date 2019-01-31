#!/usr/bin/env python
import pigpio
import time
import firebase_admin
from firebase_admin import db
from firebase_admin import credentials

# initialize modules
pi = pigpio.pi()

firebase_admin.initialize_app(options={
    'databaseURL' : 'https://my-db.firebaseio.com'
})
root = db.reference()
peripherals = root.child('peripherals')

I2C_ADDR=0x10 # tentatively

# helper to quickly decode
def dc(b):
    ENCODING = 'UTF-8'
    return b.decode(ENCODING)

# function for handling device declaration messages
def device(slave, name):
   peripherals.push({
     slave:
       {
         'name': name,
         'vars': {},
         'funcs': {}
       }
   })

# function for handling variable declaration messages
def newvar(var_id, slave, var_size, var_type, name):
    peripherals.child(slave + '/vars').push({
      var_id:
        {
          'name': name,
          'size': var_size,
          'type': var_type,
          'val':{}
        }
    })

# function for handling function declaration messages
def newfun(fun_id, slave, arg_size, arg_type, name):
    peripherals.child(slave + '/funcs').push({
      var_id:
        {
          'name': name,
          'size': arg_size,
          'type': arg_type,
        }
    })

# function for handling variable store messages
def varstore(var_id, slave, value):
    peripherals.child(slave + '/vars/' + var_id + '/val').push({
      time.ctime(): value
    })



# dummy function that just produces an error message if a function call is performed by the slave
def funcall():
    raise RuntimeWarning("The daemon has just received a function call message. The message will be ignored.")

# dictionary of above functions where the key is the 3-bit control code
funcs = {
        0b000: device,
        0b001: newvar,
        0b010: newfun,
        0b011: varstore,
        0b100: funcall
        }


# argument generator for handling device declaration messages
def device_args(data):
    return (data[1], dc(data[2:]))

# argument generator for handling variable declaration messages
def newvar_args(data):
    return (data[0] >> 3, data[1], data[2] >> 2, data[2] & 0b11, dc(data[3:]))

# argument generator for handling function declaration messages
def newfun_args(data):
    return (data[0] >> 3, data[1], data[2] >> 2, data[2] & 0b11, dc(data[3:]))

# argument generator for handling variable store messages
def varstore_args(data):
    return (data[0] >> 3, data[1], dc(data[2:]))

# dummy argument generator for function calls
def funcall_args(data):
    return ()

# dictionary of above functions where the key is the 3-bit control code
arg_gens = {
        0b000: device_args,
        0b001: newvar_args,
        0b010: newfun_args,
        0b011: varstore_args,
        0b100: funcall_args
        }

# this function i2c() gets called by the event callback - it's the top level
# function for handling received i2c messages
def i2c(id,tick):
    global pi

    # status, number of bytes recieved, and data
    status, nbytes, data = pi.bsc_i2c(I2C_ADDR)

    if b: # NOTE: maybe check some status bits here too
        opcode = data[0] # generate opcode
        func = funcs[opcode] # identify appropriate function
        arg_gen = arg_gens[opcode] # identify arg generator
        args = arg_gen(data) # generate args

        func(*args) # expand args tuple into args and call the function

i2c_cb = pi.event_callback(pigpio.EVENT_BSC, i2c)
pi.bsc_i2c(I2C_ADDR)
