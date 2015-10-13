# -*- coding: utf-8 -*-
"""
Created on Tue Oct 07 23:18:45 2014

@author: Nick
"""
from collections import deque
from threading import Thread, Lock
from datetime import datetime
from numpy import nan, isnan, abs, average, zeros
from cv2 import GaussianBlur, moments
import picamera, picamera.array
import time, bisect, cv2, serial
   

def suppressFire_callback(channel):
    x,y = nan, nan
    while isnan(x) or isnan(y):
        FireImage = abs(average(ImQueue[-1],-1) - average(ImQueue[0],-1))
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
    data = GaussianBlur(data,(3,3),2)
    mask = zeros(data.shape)
    mask[data > (data.mean() + data.max())/2.] = 1
    mom = moments(mask)
    try:
        x, y = mom['m10']/mom['m00'], mom['m01']/mom['m00']
    except ZeroDivisionError:
        x, y = nan, nan
    return x, y

def pictureQueue(res,bright,con,fps,gains):
    '''Keeps a running queue of three pictures for comparison and fire location'''
    global ImQueue, Flag
    Flag = 1
    ImQueue = deque()
    with picamera.PiCamera() as cam:
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
        cam.stop_preview()
        print 'camera is live'
        with picamera.array.PiRGBArray(cam) as output:
            count = 0
            t1 = time.time()
            for im in cam.capture_continuous(output,'rgb',use_video_port = True):
                print Flag
                count += 1
                ImQueue.append(output.array)
                if len(ImQueue) > 3:
                    ImQueue.popleft()
                output.truncate(0)
                if not count%1000:
                    print '%d fps' % int(1000/(time.time()-t1))
                    count, t1 = 0, time.time()
                if not Flag:
                    print 'camera closing'
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
    s = binaryCode((4,6))
    chksum += s%8
    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum))
    ser.write(cmd)
    time.sleep(3)
    cmd = '\xb3\x01\x07\x10\x00\x0b\x0d'
    ser.write(cmd)

def firePorts_nick(dat):
    '''Sends command to board to fire correct ports for Nick's board'''
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
	#	cam.capture('precalib.bmp')
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
		
