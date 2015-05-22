import RPi.GPIO as gpio
import time

def callback1(channel):
    print 'Channel %s triggered' % channel
    
gpio.setmode(gpio.BCM)

gpio.setup(18,gpio.IN)

gpio.input(18)

gpio.add_event_detect(18,gpio.FALLING, callback = callback1, bouncetime = 300)

while True:
    time.sleep(1)
