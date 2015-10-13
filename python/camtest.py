import cv2, time
from collections import deque
import numpy as np


def cv2Fire(im):
    data = cv2.GaussianBlur(im,(3,3),2)
    mask = np.zeros(data.shape)
    mask[data > (data.mean() + data.max())/2.]=1
    mom = cv2.moments(mask)
    try:
        x, y = mom['m10']/mom['m00'],mom['m01']/mom['m00']
    except ZeroDivisionError:
        x,y = np.nan,np.nan
    return x, y

rgbavg = 100
counter = 1

cap = cv2.VideoCapture(0)
cap.set(3,160)
cap.set(4,120)

## To Activate Automatic Calibration, Un/Comment-out the following section
## ---------------Start of Calibration-------------------

cap.set(6,30)
cap.set(14,20)

tog1 = 2
tog2 = 2
bright = 70
con = 70
cap.set(10,bright)
cap.set(11,con)
bvar = 0
cvar = 0
gmax = 100
scord = 3
mcord = 3

while ( rgbavg > 12) or (gmax > 150):
    
    if not tog1%2:
        if not tog2%2:
            bvar += 5
            cap.set(10,bright-bvar)
        else:
            bvar += 5
            cap.set(10,bright-bvar)
    else:
        if not tog2%2:
            cvar += 5
            cap.set(11,con+cvar)
            tog2 += 1
        else:
            cvar += 5
            cap.set(11,con+cvar)
            tog2 += 1

    tog1 += 1
    print counter
    counter += 1
    if counter > 3:
        cap.set(10,20)
        cap.set(11,70)
        break
    brightP = cap.get(10)
    conP = cap.get(11)
    print brightP, 'Brightness'
    print conP, 'Contrast'

    ret, img = cap.read()
    ret, img = cap.read()
    ret, img = cap.read()

    rtot = 0
    gtot = 0
    btot = 0
    gmax = 0

    xsize = int(cap.get(3))
    ysize = int(cap.get(4))
    for s in range(0,xsize/2): #These Four Lines Control Skips
        s=s*2                  # Change the 3 to how ever you want to skip
        for m in range(0,ysize/2): #plus 1
                m=m*2 #
                b,g,r = img[m,s,:]
                rtot += r
                gtot += g
                btot += b
                if g > gmax:
                    gmax = g
                    scord=s
                    mcord=m

    ravg = rtot/(xsize*ysize/4)/2.55 #Skips here, too
    gavg = gtot/(xsize*ysize/4)/2.55
    bavg = btot/(xsize*ysize/4)/2.55    
    rgbavg = (ravg + gavg + bavg)/3

    if (0 < scord < xsize) and (0 < mcord < ysize):
        b,g1,r = img[scord, mcord,:]
        b,g2,r = img[scord+1, mcord,:]
        b,g3,r = img[scord, mcord+1,:]
        b,g4,r = img[scord-1, mcord,:]
        b,g5,r = img[scord, mcord-1,:]
        gmaxarea = (g1+g2+g3+g4+g5)/5
    else:
        gmaxarea = gmax
        print 'safeguard active'
    
    print rgbavg, 'percent white'
    print gmaxarea, 'g max value'
    del s, m, xsize, ysize, r, g, b, rtot, gtot, btot, ravg, gavg, bavg

## --------------End of Calibration-------------------

ret, img = cap.read()
ret, img = cap.read()

imqueue = deque()
cnt = 0
cap.set(cv2.CAP_PROP_FPS,30)
print cap.get(cv2.CAP_PROP_FPS)
while True:
    while cnt < 2:
        ret,frame = cap.read()
        imqueue.append(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))
        cnt += 1
    ret,frame = cap.read()
    imqueue.append(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))
    img = imqueue.popleft()
    cv2.imshow('frame0',img)
    cv2.imshow('frame1',imqueue[0])
    cv2.imshow('frame2',imqueue[1])
    img = np.abs(cv2.add(img,-imqueue[-1]))%255
    fire = cv2Fire(img)
    if all(not np.isnan(x) for x in fire):
        img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
        img = cv2.circle(img,tuple(map(int,fire)),10,(0,0,255),3)
    cv2.imshow('frame',img)
    if cv2.waitKey(1) & 0xff == ord('q'):
        break

cv2.destroyAllWindows()
cap.release()
