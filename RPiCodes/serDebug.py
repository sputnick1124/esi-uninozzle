import serial, time

def serCheck():
    while ser.inWaiting():
        ser.flushInput()
    ser.write(chr(254))
    ser.write(chr(152))
    try:
        Gate = ord(ser.read())
    except TypeError:
        ser.flushInput()
        Gate = 500
    ser.write(chr(254))
    ser.write(chr(153))
    try:
        Override = ord(ser.read())
    except TypeError:
        ser.flushInput()
        Override = 500
    print Gate,Override
    return Gate, Override

def fire():
    ser.write(chr(254))
    ser.write(chr(30))
    time.sleep(2)
    ser.write(chr(254))
    ser.write(chr(29))
    print map(ord,ser.read(10))


try:
    ser = serial.Serial('/dev/ttyUSB0',baudrate = 115200, timeout = .02)
    while True:
        Gate, Override = serCheck()
##        print 'Gate',Gate,'Override',Override
        if Gate < 120:
            fire()
except KeyboardInterrupt:
    ser.write(chr(254))
    ser.write(chr(29))
    ser.close()
