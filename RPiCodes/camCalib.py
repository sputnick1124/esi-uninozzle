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
   

res = 162, 120
fps = 90
with picamera.PiCamera() as cam:
    cam.resolution = res
    cam.framerate = fps
    cam.start_preview()
    time.sleep(1)
    time.sleep(1)
    cam.stop_preview()
    bright = cam.brightness
    con = cam.contrast
    print 'Brightness: %.2f' % cam.brightness
    print 'Contrast: %.2f' % cam.contrast

    cam.start_preview()
    time.sleep(100)
    cam.stop_preview()
