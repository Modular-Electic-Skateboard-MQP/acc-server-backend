import RPi._I2C as i2c
from multiprocessing import Process, Queue

I2C_BUS = "/dev/i2c-1"
I2C_ADDR = 0x10
MSG_SIZE = 30
QUEUE_TIMEOUT = None

i2c.init(I2C_BUS)

def i2c_reader(queue):
    while True:
        msg = i2c.read(MSG_SIZE)
        if (msg.len()):
            queue.put(msg, timeout = QUEUE_TIMEOUT)

def fun(fun_id, slave, arg):
    # expects fun_id as int, slave as int, arg can be anything
    argb = list(bytes(arg))
    i2c.open(slave)
    i2c.write([(fun_id << 3) | 0b100])
    i2c.write(argb)
    i2c.close() 
