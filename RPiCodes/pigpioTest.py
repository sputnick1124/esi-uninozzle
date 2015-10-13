import pigpio

pi = pigpio.pi()
pi.set_mode(23,pigpio.INPUT)
pi.set_mode(24,pigpio.INPUT)
pi.set_mode(18,pigpio.OUTPUT)

while True:
    print pi.read(23)


