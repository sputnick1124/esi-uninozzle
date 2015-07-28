# -*- coding: utf-8 -*-
"""
Created on Tue Oct 07 23:18:45 2014

@author: Nick
"""
import picamera, picamera.array
from numpy import nan, isnan, abs, average, zeros
from cv2 import GaussianBlur, moments, imwrite
from threading import Thread, Lock
from collections import deque
import time
   

def pictureQueue(res,bright,con,fps,gains):
    '''Keeps a running queue of three pictures for comparison and fire location'''
    global ImQueue, Flag
    ImQueue = deque()
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
        cam.rotation = 180
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
		


res = 100,60              

#---


# Camera calibration
#---
fps = 10
gains, bright, con = calibrate()
#---

if __name__ == '__main__':
    try:
        lock = Lock()
        t1 = Thread(target = pictureQueue, args = (res,bright,con,fps,gains,))
        t1.daemon = True
        t1.start()
        time.sleep(1)
        while not ('ImQueue' in globals() and len(ImQueue) > 2):
            time.sleep(0.5)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print '\nkilling program...'
        Flag = 0
        t1.join()
