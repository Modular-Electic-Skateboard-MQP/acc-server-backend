#!/usr/bin/env python

import time
import firebase_admin
from firebase_admin import db
from firebase_admin import credentials
from i2c_daemon import *
from multiprocessing import Process, Queue
from os import system

system('export GOOGLE_APPLICATION_CREDENTIALS="/home/rock64/mesb-backend-keys.json"')
    
ENCODING = 'UTF-8'
QUEUE_SIZE = 10

# initialize modules
firebase_admin.initialize_app(options={
    'apiKey': "AIzaSyBJN3d0umh5zKC80gInDNP1KKEPSUoZ1F8",
    'authDomain' : "mesb-70fa5.firebaseapp.com",
    'databaseURL': "https://mesb-70fa5.firebaseio.com",
    'storageBucket': "mesb-70fa5.appspot.com",
    'messagingSenderId': "196474953476"
})
root = db.reference()

# helper to quickly decode
def dc(b):
    #return str(b).decode(ENCODING)
    return ''.join(chr(i) for i in b)

# function for handling device declaration messages
def device(slave, name):
    dev = peripherals.child(slave)
    dev.set(
        {
          'name': name,
        }
    )
    dev.child('vars')
    dev.child('funcs')

# function for handling variable declaration messages
def newvar(var_id, slave, var_size, var_type, name):
    var = peripherals.child(slave + '/vars/' + var_id)
    var.child('name').set(name)
    var.child('size').set(var_size)
    var.child('type').set(var_type)
    #var.set(
    #    {
    #      'name': name,
    #      'size': var_size,
    #      'type': var_type
    #    }
    #)
    var.child('val')

# function for handling function declaration messages
def newfun(fun_id, slave, arg_size, arg_type, name):
    fun = peripherals.child(slave + '/funcs/' + fun_id)
    fun.set(
        {
          'name': name,
          'size': arg_size,
          'type': arg_type
        }
    )

# function for handling variable store messages
def varstore(var_id, slave, value):
    t = peripherals.child(slave + '/vars/' + var_id + '/val/' + time.ctime())
    t.set(value)

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
    return (hex(data[1]), dc(data[2:]))

# argument generator for handling variable declaration messages
def newvar_args(data):
    return (hex(data[0] >> 3), hex(data[1]), data[2] >> 2, data[2] & 0b11, dc(data[3:]))

# argument generator for handling function declaration messages
def newfun_args(data):
    return (hex(data[0] >> 3), hex(data[1]), data[2] >> 2, data[2] & 0b11, dc(data[3:]))

# argument generator for handling variable store messages
def varstore_args(data):
    return (hex(data[0] >> 3), hex(data[1]), str(data[2:]))

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

if __name__ == '__main__':
    queue = Queue(QUEUE_SIZE)
    i2c_p = Process(target=i2c_reader, args=((queue),))
    i2c_p.daemon = True
    i2c_p.start()


    runs = root.child('runs')
    run = runs.child(time.ctime())
    peripherals = run.child('peripherals')
    while True:
        msg = queue.get()
        opcode = msg[0] & 0b111 # 3 LSBs of first byte
        func = funcs[opcode]
        arg_gen = arg_gens[opcode]
        args = arg_gen(msg)

        func(*args) # expand args tuple into args, call function


