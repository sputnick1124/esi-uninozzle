# -*- coding: utf-8 -*-
"""
Created on Tue Oct 07 23:18:45 2014

@author: HP
"""
from collections import deque
from scipy import average
from threading import Thread, Lock
from datetime import datetime
import RPi.GPIO as GPIO
import picamera, picamera.array
import numpy as np
import scipy.ndimage as ndimage
import scipy.misc as misc
import scipy.ndimage.filters as filters
import serial, time, bisect
   

def suppressFire_callback(channel):
    x,y = float('nan'),float('nan')
    while np.isnan(x) or np.isnan(y):
        FireImage = abs(average(ImQueue[-1],-1) - average(ImQueue[0],-1))
        x,y = findFire(FireImage)
    fo = '-'.join(map(str, datetime.now().timetuple()[:6]))
    misc.imsave('fire'+fo+'.bmp',FireImage)
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
    
    
    data = filters.gaussian_filter(data,1)
    mask = data > (data.mean() + data.max())/2.
    y, x = ndimage.center_of_mass(mask) # y,x because of (height,width) image convention
    return x, y

def pictureQueue(res,bright,con,fps):
    '''Keeps a running queue of three pictures for comparison and fire location'''
    global ImQueue, Flag
    Flag = 1
    ImQueue = deque([])
    with picamera.PiCamera() as cam:
        cam.resolution = res
        cam.brightness = bright
        cam.contrast = con
        cam.framerate = fps
        cam.start_preview()
        time.sleep(1)
        g = cam.awb_gains
        cam.iso = 200
        cam.exposure_mode = 'off'
        cam.awb_mode = 'off'
        cam.awb_gains = g
        cam.stop_preview()
        with picamera.array.PiRGBArray(cam) as output:
            t1 = time.time()
            count = 0
            for im in cam.capture_continuous(output,'rgb',use_video_port = True):
                ImQueue.append(output.array)
                if len(ImQueue) > 3:
                    ImQueue.popleft()
                output.truncate(0)
            

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
        
    BinaryPorts = [1,2,4,8,16,32,64,128]
    cmd = 0
    for port in ports:
        cmd |= BinaryPorts[port]
    return cmd

def firePorts(dat):
    '''Sends command to board to fire correct ports'''
    ser.write(chr(254))
    ser.write(chr(40))
    ser.write(chr(binaryCode(fireDict[dat])))
    time.sleep(3)
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()

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

ser = serial.Serial('/dev/ttyUSB0', baudrate = 115200, timeout = 0.02)
#---

# Map the ports to the frame grid. These may need to be derived by trial/error.
# This mapping will need to be adjusted for specific environments.
#---
portcombos = [(0, 1), (0, 1), (6, 7), (3, 7), (2, 7), 
#               ------------------------------------------
              (0, 1), (0, 1), (1, 7), (3, 6), (2, 6), 
#               ------------------------------------------
              (0, 1), (0, 1), (0, 3), (2, 3), (3, 5), 
#               ------------------------------------------
              (0, 1), (0, 1), (0, 6), (1, 3), (1, 2), 
#               ------------------------------------------
              (0, 1), (0, 1), (0, 1), (0, 3), (0, 2)]
              
grid = [(x,y) for y in range(5) for x in range(5)] # 5X5 grid locations
fireDict = dict(zip(grid,portcombos)) # Hash grid locations to ports

xsize , ysize = (160,120) # this block of code constructs the protection grid divisions
xsplit = xsize / 5
ysplit = ysize / 5
xdivs = range(0, xsize + xsplit, xsplit)
ydivs = range(0, ysize + ysplit, ysplit)

#---


# Camera calibration
#---

res = (160,120)
fps = 32
with picamera.PiCamera() as cam:
    cam.resolution = res
    cam.framerate = fps
    cam.start_preview()
    time.sleep(1)
    g = cam.awb_gains
    cam.iso = 300
    cam.exposure_mode = 'off'
    cam.awb_mode = 'off'
    cam.awb_gains = g
    with picamera.array.PiRGBArray(cam) as output:
        cam.capture(output,'rgb',use_video_port = True)
##        avg_luminance = average(output.array[...,0])
        avg_luminance = average(output.array)
        while avg_luminance > 70:
            if cam.brightness >= 5:
                cam.brightness -= 5
            if cam.contrast <= 95:
                cam.contrast += 5
            if cam.brightness == 0 and cam.contrast == 100:
                break
            avg_luminance = average(output.array)
    time.sleep(1)
    cam.stop_preview()
    bright = cam.brightness
    con = cam.contrast
    print 'Brightness: %.2f' % cam.brightness
    print 'Contrast: %.2f' % cam.contrast
#---

try:
    lock = Lock()
    t1 = Thread(target = pictureQueue, args = (res,bright,con,fps,))
    t1.setDaemon(True)
    t1.start()
    GPIO.add_event_detect(gatePin, GPIO.FALLING, callback = suppressFire_callback)#, bouncetime = 300)
##    GPIO.add_event_detect(overridePin, GPIO.FALLING, callback = fireAllPorts_callback,bouncetime = 500)
##    input('Press enter to exit program')
##    GPIO.cleanup()
except KeyboardInterrupt:
    GPIO.cleanup()
    ser.close
    Flag = 0
    t1.join()
