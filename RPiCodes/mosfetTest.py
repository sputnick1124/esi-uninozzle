import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)
pins = [21,20,26,16,19,13,12,6,5]
gpio.setup(pins,gpio.OUT)
gpio.output(pins,0)
gpio.cleanup()
