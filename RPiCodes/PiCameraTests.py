# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 21:55:53 2014

@author: HP
"""

import picamera, io, PIL.Image,time

#count = 0
with picamera.PiCamera() as cam:
    stream = picamera.PiCameraCircularIO(cam,seconds=5)
    cam.framerate = 60
    cam.start_recording(stream,format='h264')
    time.sleep(10)
