#!/usr/bin/python2.7

import sys
from cv2 import GaussianBlur, moments, imread
from numpy import nan, zeros

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

filename = sys.argv[1]
imgdata = imread(filename,0)
print findFire(imgdata)
