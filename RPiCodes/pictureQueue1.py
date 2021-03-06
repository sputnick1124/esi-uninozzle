import picamera, picamera.array, time
import scipy.misc as misc
from scipy import average
from collections import deque

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
                
##                ImQueue.append(average(output.array,-1))
                ImQueue.append(output.array)
##                ImQueue.append(output.array[...,1])
                if len(ImQueue) > 3:
##                    FireImage = abs(ImQueue[-1] - ImQueue[0])
                    ImQueue.popleft()
                output.truncate(0)
                count += 1
                if time.time() - t1 > 10:
                    break
            print 'Captured %d images in %f seconds' % (count,time.time()-t1)

pictureQueue((160,120),0,100,90)

for i,im in enumerate(ImQueue):
	misc.imsave('testG%d.bmp' % i,im)

misc.imsave('testdiff.bmp',abs(average(ImQueue[-1],-1)-average(ImQueue[0],-1)))
