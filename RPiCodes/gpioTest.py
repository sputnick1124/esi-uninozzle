import RPi.GPIO as gpio
import time
    
def callback1(channel):
    print gpio.input(channel)
    if gpio.input(channel):
        t1 = time.time()
        while time.time()-t1<0.1:
            print gpio.input(channel)
            time.sleep(0.01)
gpio.setmode(gpio.BCM)

gate = 24

gpio.setup(gate,gpio.IN,pull_up_down=gpio.PUD_OFF)

gpio.input(gate)

gpio.add_event_detect(gate,gpio.FALLING, callback = callback1, bouncetime = 300)

try:
    while True:
        time.sleep(0.01)
#        print gpio.input(gate)
except KeyboardInterrupt:
    pass
