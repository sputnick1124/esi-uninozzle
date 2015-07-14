import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BCM)
pins = [21,20,26,16,19,13,12]
mixer = 6
gpio.setup(pins+[mixer],gpio.OUT)
gpio.output(pins,0)
t1 = 3
t2 = 0.5
#pins = [21]
for pin in pins:
	print pin
	gpio.output([pin,mixer],1)
	time.sleep(t1)
	gpio.output([pin,mixer],0)
	time.sleep(t2)
gpio.cleanup()

