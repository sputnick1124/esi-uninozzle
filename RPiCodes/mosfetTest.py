import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)
pins = [21,20,26,16,19,13,12,6,5]
gate = 24
gpio.setup(gatePin,GPIO.IN,pull_up_down = GPIO.PUD_UP)
gpio.setup(pins,gpio.OUT)
gpio.output(pins,0)

#gpio.cleanup()
