import io
import time
import threading
import picamera
import PIL.Image as Image
import scipy.misc as misc
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
import ImageChops, sys, ImageDraw, serial, time, bisect

# Create a pool of image processors
done = False
lock = threading.Lock()
pool = []

def findFire(A,C):
    '''Locates the brightest area in the frame by applying a differential
    gaussian filter and creating a byte array of light vs dark. The centroid
    of the light region is found and returned as the location of the fire
    
    Input:
        im - PIL image numpy array
    
    Output:
        x,y - Cartesian coordinates representing the location (in pixels)
                of the centroid of the brightest pixels in the grayscale
                representation of im. Only the brightest 25% are used'''
    im = ImageChops.difference(A,C)
    data = misc.fromimage(im,flatten = 1)
    data = filters.gaussian_filter(data,2)
    mask = data > (data.mean() + data.max())/2.        
    y, x = ndimage.center_of_mass(mask) # y,x because of (height,width) image convention
    return x, y

class ImageProcessor(threading.Thread):
    def __init__(self):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.start()

    def run(self):
        # This method runs in a separate thread
        global done
        global count
        global countT
        global x, y, A, B, C
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
                    #Read the image and do some processing on it
                    if count == 0:
                        A = Image.open(self.stream)
                        A.save('a.jpg')
                    elif count == 1:
                        B = Image.open(self.stream)
                        B.save('b.jpg')
                    else:
                        C = Image.open(self.stream)
                        C.save('c.jpg')
                    count += 1
                    countT += 1
                    if not count%3:
                        count = 0
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the pool
                    with lock:
                        pool.append(self)

def streams(t1):
    while time.time() - t1 < 10:
        with lock:
            if pool:
                processor = pool.pop()
            else:
                processor = None
        if processor:
            yield processor.stream
            processor.event.set()
        else:
            # When the pool is starved, wait a while for it to refill

            time.sleep(0.1)
count,countT = 0,1
with picamera.PiCamera() as camera:
    pool = [ImageProcessor()]
    camera.resolution = (120,160)
    camera.framerate = 60
    time.sleep(2)
    t1 = time.time()
    camera.capture_sequence(streams(t1), use_video_port=True)
while pool:
    with lock:
        processor = pool.pop()
    processor.terminated = True
    processor.join()
print '%d pictures captured in %.2f seconds' % (countT,time.time() - t1)
