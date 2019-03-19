import RPi._I2C as i2c
from multiprocessing import Process, Queue
import time

I2C_BUS = "/dev/i2c-1"
I2C_ADDR = 0x10
MSG_SIZE = 30
QUEUE_TIMEOUT = None

#bus = i2c.init(I2C_BUS)
#bus.open(I2C_ADDR)

def i2c_reader(queue):
    # declare accessory with name "Demo" and i2c addr 0x20
    msg = [0x00,0x20,ord('D'),ord('e'),ord('m'),ord('o')]
    queue.put(msg, timeout = QUEUE_TIMEOUT)

    # declare variable with identifier 1, slave id 0x20, 1 byte, type int, name count
    msg = [0b00001000 | 0b001, 0x20, 0b00000100 | 0b00,ord('C'),ord('o'),ord('u'),ord('n'),ord('t')]
    queue.put(msg, timeout = QUEUE_TIMEOUT)


    count = 0
    while True:
        # report count and increment
        msg = [0b00001000 | 0b011, 0x20, count & 0xFF]
        if len(msg):
            queue.put(msg, timeout = QUEUE_TIMEOUT)
            count += 1
            time.sleep(1)

