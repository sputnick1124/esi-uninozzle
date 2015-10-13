import RPi.GPIO as gpio
import time

def simpleFire(ports,T):
	if not isinstance(ports,tuple):
		ports = (ports,)
	pin_nums = [12,19,26,21,20,16,13]
	sols = [pin_nums[i] for i in ports] + [6]
	gpio.output(sols,1)
	time.sleep(T)
	gpio.output(sols,0)

gpio.setmode(gpio.BCM)
powder_mixer = [6]
pin_nums = [12,19,26,21,20,16,13]
gpio.setup(pin_nums+powder_mixer,gpio.OUT)
gpio.output(pin_nums+powder_mixer,0)

T = input('Fire time? ')

try:
	while True:
		try:   
			ports = input('Enter ports (comma-separated list): ')
			simpleFire(ports,T)
		except KeyboardInterrupt:
			T = input('\nFire Time? ')
except KeyboardInterrupt:
	gpio.cleanup()
