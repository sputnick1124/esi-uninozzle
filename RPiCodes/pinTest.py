import RPi.GPIO as gpio
import time

def announce(channel):
	print 'UVTRON LOW',
	print time.time() - T1

gpio.setmode(gpio.BCM)

uv_tron = 24
sols = [21, 20, 26, 16, 19, 13, 12, 6]
led = 5

gpio.setup(sols+[led],gpio.OUT)
gpio.setup(uv_tron,gpio.IN,pull_up_down=gpio.PUD_UP)

T1 = time.time()
while True:
	uv_state = gpio.input(uv_tron)
	if not uv_state:
		print uv_state,
		print time.time() - T1


