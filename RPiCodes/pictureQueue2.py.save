import picamera, picamera.array, time
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
        samp = 30
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
                if time.time() - t1 > samp:
                    break
            print 'Captured %d images in %f seconds' % (count,time.time()-t1)
            print 'Effective frame rate: %d fps' % int(count/float(samp))

pictureQueue((100,60),0,100,90)

