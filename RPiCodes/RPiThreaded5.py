# -*- coding: utf-8 -*-
"""
Created on Tue Oct 07 23:18:45 2014

@author: Nick
"""
from collections import deque
from threading import Thread, Lock
from datetime import datetime
import RPi.GPIO as GPIO
import picamera, picamera.array
import numpy as np
import serial, time, bisect, cv2
   

def suppressFire_callback(channel):
    x,y = float('nan'),float('nan')
    while np.isnan(x) or np.isnan(y):
        FireImage = np.abs(np.average(ImQueue[-1],-1) - np.average(ImQueue[0],-1))
        x,y = findFire(FireImage)
#    fo = '-'.join(map(str, datetime.now().timetuple()[:6]))
#    misc.imsave('fire'+fo+'.bmp',FireImage)
    xdivtmp, ydivtmp = xdivs[:], ydivs[:]
    bisect.insort(xdivtmp,x)   # Insert the fire coordinates into the protection grid
    bisect.insort(ydivtmp,y)
    xzone = xdivtmp.index(x) - 1   # Find the grid coordinates
    yzone = ydivtmp.index(y) - 1
    del xdivtmp, ydivtmp             
    firePorts((xzone,yzone))
    print 'Fire at (%.2f,%.2f) in zone %d,%d\nFiring ports %d & %d' % ((x,y,xzone,yzone,) + fireDict[(xzone,yzone)])

def findFire(data):
    '''Locates the brightest area in the frame by applying a differential
        gaussian filter and creating a byte array light vs dark. The centroid
        of the light region is found and returned as the location of the fire'''
    data = cv2.GaussianBlur(data,(3,3),2)
    mask = np.zeros(data.shape)
    mask[data > (data.mean() + data.max())/2.] = 1
    mom = cv2.moments(mask)
    try:
        x, y = mom['m10']/mom['m00'], mom['m01']/mom['m00']
    except ZeroDivisionError:
        x, y = np.nan, np.nan
    return x, y

def pictureQueue(res,bright,con,fps):
    '''Keeps a running queue of three pictures for comparison and fire location'''
    global ImQueue, Flag
    Flag = 1
    ImQueue = deque()
    with picamera.PiCamera() as cam:
        cam.resolution = res
        cam.brightness = bright
        cam.contrast = con
        cam.framerate = fps
        cam.start_preview()
        time.sleep(1)
        cam.stop_preview()
        print 'camera is live'
        with picamera.array.PiRGBArray(cam) as output:
            count = 0
            t1 = time.time()
            for im in cam.capture_continuous(output,'rgb',use_video_port = True):
                count += 1
                ImQueue.append(output.array)
                if len(ImQueue) > 3:
                    ImQueue.popleft()
                output.truncate(0)
                if not count%1000:
                    print '%d fps' % int(1000/(time.time()-t1))
                    count, t1 = 0, time.time()
            

def binaryCode(ports):
    '''Accepts a tuple of integers 0-7 signifying the ports desired. Allows
    user to fire all ports on the solenoid board with a single 
    command. Returns one byte character to set the status of all ports 
    simultaneously. See docs on the Relay Pros website.
    
    Input:
        ports - Tuple of integers
        
    Output:
        cmd - Integer representation of unicode character.
    
    Example usage: binaryCode((0,4,6)) returns 81. User then sends chr(81)
        to the solenoid board which interprets the unicode character as an 
        8-bit binary switch, turning on solenoids 0, 4, and 6.
    
            bin(81) = '0b1010001' = 0 1 0 1 0 0 0 1
                                    7 6 5 4 3 2 1 0'''
        
    cmd = 0
    for port in ports:
        cmd |= 1<<port
    return cmd

def firePorts(dat):
    '''Sends command to board to fire correct ports'''
    chksum = 11
#    s = binaryCode(fireDict[dat])
    s = binaryCode((4,6))
    chksum += s%8
#    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum))
    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum))
    ser.write(cmd)
    time.sleep(3)
    cmd = '\xb3\x01\x07\x10\x00\x0b\x0d'
    ser.write(cmd)	


def fireAllPorts_callback(channel):
    '''Sends command to fire all ports in case of override'''
    ser.write(chr(254))
    ser.write(chr(30))
    time.sleep(3)
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()


# Set up serial connection, gpio pins
#---
gatePin = 18
overridePin = 11
GPIO.setmode(GPIO.BCM)
GPIO.setup(gatePin,GPIO.IN,pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(overridePin,GPIO.IN,pull_up_down = GPIO.PUD_DOWN)

ser = serial.Serial('/dev/ttyAMA0', baudrate = 115200, timeout = 0.02)
#---

# Map the ports to the frame grid. These may need to be derived by trial/error.
# This mapping will need to be adjusted for specific environments.
#---
portcombos = [(1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (2, 4), (4, 5), (5, 6), (6, 7)] 

res = 100,60              
xgrid, ygrid = 9, 1
grid = [(x,y) for y in range(ygrid) for x in range(xgrid)] # (xgrid) x (ygrid) grid locations
fireDict = dict(zip(grid,portcombos)) # Hash grid locations to ports

xsize , ysize = res # this block of code constructs the protection grid divisions
xsplit = xsize / xgrid
ysplit = ysize / ygrid
xdivs = range(0, xsize + xsplit, xsplit)
ydivs = range(0, ysize + ysplit, ysplit)

#---


# Camera calibration
#---
fps = 90
with picamera.PiCamera() as cam:
    cam.resolution = res
    cam.framerate = fps
    cam.start_preview()
    time.sleep(1)
    cam.stop_preview()
    bright = cam.brightness
    con = cam.contrast
    cam.start_preview()
    time.sleep(1)
    cam.stop_preview()
#---

try:
    lock = Lock()
    t1 = Thread(target = pictureQueue, args = (res,bright,con,fps,))
    t1.setDaemon(True)
    t1.start()
    GPIO.add_event_detect(gatePin, GPIO.FALLING, callback = suppressFire_callback, bouncetime = 300)
##    GPIO.add_event_detect(overridePin, GPIO.FALLING, callback = fireAllPorts_callback,bouncetime = 500)
    time.sleep(1)
#    input('Press enter to exit program')
#    GPIO.cleanup()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    ser.close
    Flag = 0
    t1.join()
