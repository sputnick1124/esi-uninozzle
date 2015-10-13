import time #All libraries must be installed on the PC and then imported at the top of the code
import serial

ser = serial.Serial('/dev/ttyUSB0') #Inizalize Serial Port. The 0 is the port number. This will may if you change computers.
ser.baudrate = 115200 
ser.timeout = .02

##ser.write(chr(254)) #Fire All
##ser.write(chr(30))

T1 = input('Fire time? ')

def binaryCode(ports):
    BinaryPorts = [1,2,4,8,16,32,64,128]
    cmd = 0
    if not isinstance(ports,tuple):
        return BinaryPorts[ports]
    for port in ports:
        cmd |= BinaryPorts[port]
    return cmd

def serialOut(ser,cmd):
    ser.write(chr(254))
    ser.write(chr(40))
    ser.write(chr(binaryCode(cmd)))
    time.sleep(T1)
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()
try:
    while True:
        try:   
            cmd = input('Enter ports (comma-separated list): ')
            serialOut(ser,cmd)
        except KeyboardInterrupt:
            T1 = input('\nFire Time? ')
except KeyboardInterrupt:
    ser.close()
