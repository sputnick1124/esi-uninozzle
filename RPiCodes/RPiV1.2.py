# -*- coding: utf-8 -*-
"""
Created on Tue Oct 07 23:18:45 2014

@author: Nick
"""
from threading import Thread, Lock
from collections import deque
import picamera, picamera.array
import serial, time, bisect
import RPi.GPIO as GPIO
from datetime import datetime
from numpy import nan, isnan, abs, average, zeros
from cv2 import GaussianBlur, moments, imwrite
   

def suppressFire_callback(channel):
    x,y = nan, nan
    while isnan(x) or isnan(y):
        if GPIO.input(channel):
            return
#        FireImage = abs(average(ImQueue[-1],-1) - average(ImQueue[0],-1))
        FireImage = average(ImQueue[0],-1)
        x,y = findFire(FireImage)
#    fo = '-'.join(map(str, datetime.now().timetuple()[:6]))
#    imwrite('fire'+fo+'.bmp',FireImage)
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
    data = GaussianBlur(data,(3,3),2)
    mask = zeros(data.shape)
    mask[data > (data.mean() + data.max())/1.5] = 1
    mom = moments(mask)
    imwrite('mask{0}{1}{2}.bmp'.format(mom['m00'],mom['m02'],mom['m20']),mask)
    if mom['m00']:
        x, y = mom['m10']/mom['m00'], mom['m01']/mom['m00']
    else:
        x, y = nan, nan
    return x, y

def pictureQueue(res,bright,con,fps,gains):
    '''Keeps a running queue of three pictures for comparison and fire location'''
    global ImQueue, Flag
    ImQueue = deque()
    GPIO.output(sigPin,1)
    window = (1400,150,300,180)
    with picamera.PiCamera() as cam:
        cam.preview_fullscreen = False
        cam.preview_window = window
        cam.iso = 800
        cam.awb_mode = 'off'
        cam.awb_gains = gains
        cam.resolution = res
        cam.shutter_speed = 100
        cam.brightness = bright
        cam.contrast = con
        cam.framerate = fps
        cam.start_preview()
        time.sleep(1)
        print 'camera is live'
        Flag = 1
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
                if not Flag:
                    cam.stop_preview()
                    break
    print 'camera closed'

def binaryCode(ports):
    '''Accepts a tuple of integers 0-7 signifying the ports desired.
    
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

def firePorts_jeff(dat):
    '''Sends command to board to fire correct ports for Jeff's board (serial)'''
    chksum = 11
#    s = binaryCode(fireDict[dat])
    s = binaryCode((4,6)) # for testing
    chksum += s%8
    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum))
    ser.write(cmd)
    ser.flushOutput()
    GPIO.output(sigPin,1)
    time.sleep(3)
    cmd = '\xb3\x01\x07\x10\x00\x0b\x0d'
    ser.write(cmd)
    ser.flushOutput()
    GPIO.output(sigPin,0)

def firePorts_nick(dat):
    '''Sends command to board to fire correct ports for Nick's board'''
    ser.write(chr(254))
    ser.write(chr(40))
    ser.write(chr(binaryCode(fireDict[dat])))
    time.sleep(3)
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()

def firePorts_darlington(dat):
    for pin in fireDict[dat]:
        GPIO.output(solPins[pin],1)
#    GPIO.output([sol0,sol2],1)
    GPIO.output(sigPin,1)
    time.sleep(3)
#    GPIO.output([sol0,sol2],0)
    for pin in fireDict[dat]:
        GPIO.output(solPins[pin],0)
    GPIO.output(sigPin,0)

def fireAllPorts_callback(channel):
    '''Sends command to fire all ports in case of override'''
    ser.write(chr(254))
    ser.write(chr(30))
    time.sleep(3)
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()

def calibrate():
	rgbavg = 100
	counter = 1
	tog1 = 2
	tog2 = 2
	
	with picamera.PiCamera() as cam:
		cam.resolution = (100,60)
		cam.start_preview()
		time.sleep(1)
		cam.iso = 800
		cam.shutter_speed = 100
		cam.framerate = 30
		gains = cam.awb_gains
		cam.awb_mode = "off"
		cam.awb_gains = gains
		bright = 70
		con = 70
		cam.contrast = con
		cam.brightness = bright
		bvar = 0
		cvar = 0
		gmax = 100
		scord = 3
		mcord = 3
		with picamera.array.PiRGBArray(cam) as output:
			while rgbavg > 12 or gmax > 150:
				if not tog1%2:
					if not tog2%2:
						bvar += 5
						cam.brightness = bright + bvar
					else:
						bvar += 5
						cam.brightness = bright - bvar
				else:
					if not tog2%2:
						cvar += 5
						cam.contrast = con + cvar
						tog2 += 1
					else:
						cvar += 5
						cam.contrast = con - cvar
						tog2 += 1
				tog1 += 1
				print counter
				counter += 1
				if counter > 6:
					cam.brightness = 20
					cam.contrast = 70
					break
				brightP = cam.brightness
				conP = cam.contrast
				cam.capture(output,'rgb',use_video_port=True)
				img = output.array
				output.truncate(0)
				rtot, gtot, btot, gmax = 0, 0, 0, 0
				ysize,xsize = cam.resolution
				for s in range(xsize/2):
					s *= 2
					for m in range(ysize/2):
						m *= 2
						r,g,b = img[s, m]
						rtot += r
						gtot += g
						btot += b
						if g > gmax:
							gmax = g
							scord = s
							mcord = m
		
				ravg = rtot/(xsize*ysize/4)/2.55
				gavg = gtot/(xsize*ysize/4)/2.55
				bavg = btot/(xsize*ysize/4)/2.55
				rgbavg = (ravg + gavg + bavg)/3
		
				if (0 < scord < xsize) and (0 < mcord < ysize):
					r, g1, b = img[scord,mcord]
					r, g2, b = img[scord+1, mcord+1]
					r, g3, b = img[scord, mcord+1]
					r, g4, b = img[scord-1, mcord]
					r, g5, b = img[scord, mcord-1]
					gmaxarea = (g1 + g2 + g3 + g4 + g5)/5.
				else:
					gmaxarea = gmax
					print 'safeguard active'
		
				print rgbavg, 'percent white'
				print gmaxarea, 'g max area'
	#	cam.capture('postcalib.bmp')
		cam.stop_preview()
		cam.start_preview()	
		time.sleep(2)
		cam.stop_preview()
		return gains, bright, con
		


# Set up serial connection, gpio pins
#---
gatePin = 23
sigPin = 5
overridePin = 11
solPins = (6, 13, 16, 20, 26, 19, 12, 21)
sol0, sol1, sol2, sol3, sol4, sol5, sol6, sol7 = solPins
GPIO.setmode(GPIO.BCM)

GPIO.setup(gatePin,GPIO.IN,pull_up_down = GPIO.PUD_UP)
GPIO.setup(overridePin,GPIO.IN,pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sigPin,GPIO.OUT)
GPIO.setup(solPins,GPIO.OUT)
for pin in solPins:
    GPIO.output(pin,0)

ser = serial.Serial('/dev/ttyAMA0', baudrate = 115200, timeout = 0.001)
#---

# Map the ports to the frame grid. These may need to be derived by trial/error.
# This mapping will need to be adjusted for specific environments.
#---
portcombos = [(5, 6), (5, 6), (5, 6), (5, 6), (5, 6), (3, 5), (2, 3), (3, 4), (0, 1)] 
#portcombos = portcombos[::-1]
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
gains, bright, con = calibrate()
#---

firePorts = firePorts_darlington
if __name__ == '__main__':
    try:
        lock = Lock()
        t1 = Thread(target = pictureQueue, args = (res,bright,con,fps,gains,))
#        t1.setDaemon(True)
        t1.daemon = True
        t1.start()
        GPIO.add_event_detect(gatePin, GPIO.FALLING, callback = suppressFire_callback, bouncetime = 300)
##        GPIO.add_event_detect(overridePin, GPIO.FALLING, callback = fireAllPorts_callback,bouncetime = 500)
        time.sleep(1)
        while not ('ImQueue' in globals() and len(ImQueue) > 2):
            time.sleep(0.5)
        GPIO.output(sigPin,0)
#        input('Press enter to exit program')
#       GPIO.cleanup()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print '\nkilling program...'
        GPIO.cleanup()
        ser.close
        Flag = 0
        t1.join()
