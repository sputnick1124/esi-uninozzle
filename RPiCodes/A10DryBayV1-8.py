#This code written using Python 2.7.5 for WindowsXP

# Import all of the modules needed to use serial, do image processing, etc.
import ImageChops, sys, ImageDraw, serial, time, bisect, cv2, scipy
from VideoCapture import Device
from datetime import datetime
import PIL.Image
import numpy as np
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters

# Some helpful functions to make the code easier to read, follow, and modify
def findFire(im):
    '''Locates the brightest area in the frame by applying a differential
    gaussian filter and creating a byte array light vs dark. The centroid
    of the light region is found and returned as the location of the fire
    
    Input:
        im - PIL image numpy array
    
    Output:
        x,y - Cartesian coordinates representing the location (in pixels)
                of the centroid of the brightest pixels in the grayscale
                representation of im. Only the brightest 25% are used'''
    
    data = scipy.misc.fromimage(im,flatten = 1)
    data = filters.gaussian_filter(data,2)
    mask = data > (data.mean() + data.max())/2.        
    y, x = ndimage.center_of_mass(mask) # y,x because of (height,width) image convention
    return x, y
    
    
def binaryCode(ports):
    '''Accepts a tuple of integers 0-7 signifying the ports desired. Allows
    user to fire all ports on the solenoid board with a single 
    command. Returns one byte character to set the status of all ports 
    simultaneously. See docs on the Relay Pros website.
    
    Input:
        ports - Tuple of integers
        
    Output:
        cmd - Integer representation of unicode character.
    
    Example usage: binaryCode((0,4,6)) returns 81. User then sends chr(81)
        to the solenoid board which interprets the unicode character as an 
        8-bit binary switch, turning on solenoids 0, 4, and 6.
    
            bin(81) = '0b1010001' = 0 1 0 1 0 0 0 1
                                    7 6 5 4 3 2 1 0'''
        
    BinaryPorts = [1,2,4,8,16,32,64,128]
    cmd = 0
    for port in ports:
        cmd |= BinaryPorts[port]
    return cmd


def serialOut(dat, Dist1, Dist2, fireDict, t2):
    '''Sends serial command to board to fire selected solenoids. The option
    exists to incorporate the distance of the fire into the process to 
    potentially increase accuracy.
    
    Inputs:
        dat - Tuple. (x,y) coordinates of protection grid area where fire
                is located. Each coordinate is on a zero-based index (i.e.-
                x and y may only be [0-4]
        Dist1 - Unicode character. Read from pinout on board
        Dist2 - Unicode character. Read from pinout on board
        FireDict - Dictionary key-value pairs. Keys are protection grid
                coordinates. Values are solenoid port combinations.
        t2 - Time of detection. Time gathered at moment gate opens'''
    
#        if Dist1 < 100 and Dist2 > 100:#Check to see which distance detectors have activated
#            #presently, these are broken into 3 sections. Short if the short detector has activated...
#            #Medium if the short AND long detectors have activated, and Long for the long detector only.
#            print "Short"
#            ser.write(chr(254))
#            ser.write(chr(1))
#            ser.write(chr(254))
#            ser.write(chr(2))
#                    
#        elif Dist1 < 100 and Dist2 < 100:
#            print "Medium"
#            ser.write(chr(254))
#            ser.write(chr(1)) #Firing codes for both boards can be found on the Relay Pros website
#            ser.write(chr(254))
#            ser.write(chr(3))
#
#        elif Dist1 > 100 and Dist2 < 100:
#            print "Long"
#            ser.write(chr(254))
#            ser.write(chr(0))
#            ser.write(chr(254))
#            ser.write(chr(3))
#        
#        else:
#            print "Long, No Detect" #If the fire is out of range of either detector, it defaults to Long.
#            ser.write(chr(254))
#            ser.write(chr(0))
#            ser.write(chr(254))
#            ser.write(chr(3))
 
    t3 = time.clock();
    ser.write(chr(254))
    ser.write(chr(40)) # Lets the board know that all ports are to be 
                       # assigned silmultaneously
    ser.write(chr(binaryCode(fireDict[dat])))
    print 'Location: ' + str(dat) + ', Firing: ' + ' & '.join(map(str, fireDict[dat]))
    t4=time.clock();
    
    time.sleep(3) #Duration of Burst, in seconds
    print 'Speed of detect-to-activation start was:', t3-t2
    print 'Speed of detect-to-activation end was:', t4-t2

def MainLoop(ir0):
    '''Main function check if there is a fire and calls the other functions as
    necessary to put it out. Process flow:
                            Read "Gate" pin
                                   |
        "Open"  ---------------------------------------- "Closed"
           |                                                |
      Take a picture                              Read "Override" pin
    and find the fire                                       |                        
           |                           "Override"  -------------------  "Okay"
    Send command to                        |                               |
    board to suppress                Fire all ports                 Save a new 
           |                               |                    reference image
            ----------- Return ------------                             |
                                                                     Iterate
    '''
    xsize , ysize = ir0.size   # this block of code constructs the protection grid divisions
    xsplit = xsize / 5
    ysplit = ysize / 5
    xdivs = range(0, xsize + xsplit, xsplit)
    ydivs = range(0, ysize + ysplit, ysplit)
    
    while True:
#            ser.write(chr(254))
#            ser.write(chr(150))
#            Dist1 = ser.read(10)
#            ser.write(chr(254))
#            ser.write(chr(151))
#            Dist2 = ser.read(10)
        ser.flushInput()
        ser.write(chr(254))
        ser.write(chr(152))
        Gate = ser.read(10) # Read "Gate" pin
##            Dist1 = ord(Dist1)
##            Dist2 = ord(Dist2)
        Dist1 = 0
        Dist2 = 0
        try:
            Gate = ord(Gate)
        except TypeError:
            print Gate

        if not Gate < 120: # If "Gate" is not open
            if 'ir1' in locals(): # if there exists a variable 'ir1' (i.e. 
                ir0 = ir1           # it is not on the first iteration)
            ir1 = cam0.getImage()   # Always take a new picture for reference
            
            ser.write(chr(254))
            ser.write(chr(153))
            Override = ser.read(10)
            Override = ord(Override)
            if Override < 120:      # If "Override" has bee triggered
                print 'OVERRIDE - FIRE ALL'
                ser.write(chr(254))
                ser.write(chr(30))  # Dump all ports
                time.sleep(1)
                ser.write(chr(254)) # Closes all ports.
                ser.write(chr(29))
                ser.write(chr(254))
                ser.write(chr(29))
                ser.flushInput()
            continue    # If no Gate or Override, loop iterates here
        # If this executes, the gate is open and there is fire.
        t2 = time.clock()            
        ir2 = cam0.getImage()   # Take a picture of the fire
        ira = ImageChops.difference(ir0,ir2) # Subtract the reference image
        
        xx,yy = findFire(ira)   # Locate the fire
        
        if not np.isnan(xx) and not np.isnan(yy):   # There is a small chance there is no fire in the frame
            xdivtmp, ydivtmp = xdivs[:], ydivs[:]
            bisect.insort(xdivtmp,xx)   # Insert the fire coordinates into the protection grid
            bisect.insort(ydivtmp,yy)
            xzone = xdivtmp.index(xx) - 1   # Find the grid coordinates
            yzone = ydivtmp.index(yy) - 1
            del xdivtmp, ydivtmp            
            
            dat = xzone, yzone
            Read = serialOut(dat, Dist1, Dist2, fireDict, t2) #Assumes Cameras are Upside Down
            if (Read != ""):
                    xarea = xzone*(xsize/5) #Calculates Rectangle
                    yarea = yzone*(ysize/5)
                                                
                    ser.write(chr(254))#Switches Serial Off.
                    ser.write(chr(29))
                    ser.write(chr(254))
                    ser.write(chr(29))
                    ser.flushInput()
                    draw = ImageDraw.Draw(ira)#Initilizes Draw Class
                    draw.rectangle((xarea,yarea,xarea+(xsize/5),yarea+(ysize/5)),outline=128) #Highlights Trigger Zone
                    fo = '-'.join(map(str, datetime.now().timetuple()[:6]))
                    ira.save('fire'+fo+'.bmp')
                    del ir0, ir1, ira
                    return

        else:
            if 'ir1' in locals():
                ir0 = ir1


try:
    cam0 = Device(0,0)

    t0=time.clock();
    firenum = 1
    fireports = [0, 0, 0, 0, 0, 0, 0, 0]
    # Map the ports to the frame grid. These may need to be derived by trial/error.
    # This mapping will need to be adjusted for specific environments.
    portcombos = [(0, 1), (0, 1), (6, 7), (3, 7), (2, 7), 
#               ------------------------------------------
                  (0, 1), (0, 1), (1, 7), (3, 6), (2, 6), 
#               ------------------------------------------
                  (0, 1), (0, 1), (0, 3), (2, 3), (3, 5), 
#               ------------------------------------------
                  (0, 1), (0, 1), (0, 6), (1, 3), (1, 2), 
#               ------------------------------------------
                  (0, 1), (0, 1), (0, 1), (0, 3), (0, 2)]
                  
    grid = [(x,y) for y in range(5) for x in range(5)] # 5X5 grid locations
    fireDict = dict(zip(grid,portcombos)) # Hash grid locations to ports
    
    print 'Startup time:', t0

    ser = serial.Serial('COM3') #Inizalize Serial Port. The 0 is the port number. This will may if you change computers.
    ser.baudrate = 115200 
    ser.timeout = .02

    ser.write(chr(254))
    ser.write(chr(33))
    print ord(ser.read(10))
   

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
        brightP = cap.get(10)
        conP = cap.get(11)
        print brightP, 'Brightness'
        print conP, 'Contrast'

        ret, img = cap.read()
        ret, img = cap.read()
        ret, img = cap.read()

        cv2.imwrite("irCalib.bmp", img)

        ir0 = PIL.Image.open("irCalib.bmp")

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
                    pix = ir0.load()
                    r,g,b = pix[s,m]
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
            r,g1,b = pix[scord, mcord]
            r,g2,b = pix[scord+1, mcord]
            r,g3,b = pix[scord, mcord+1]
            r,g4,b = pix[scord-1, mcord]
            r,g5,b = pix[scord, mcord-1]
            gmaxarea = (g1+g2+g3+g4+g5)/5
        else:
            gmaxarea = gmax
            print 'safeguard active'
        
        print rgbavg, 'percent white'
        print gmaxarea, 'g max value'
        
        del ir0, s, m, xsize, ysize, pix, r, g, b, rtot, gtot, btot, ravg, gavg, bavg

    ## --------------End of Calibration-------------------
    
    ret, img = cap.read()
    ret, img = cap.read()
    cv2.imwrite("irFirstImage.bmp", img)

    cv2.destroyAllWindows() 
    cv2.VideoCapture(0).release()

    t1=time.clock();
    print 'time of calibration:', t1

    cam0.setResolution(160,120)
    ir0 = PIL.Image.open("irFirstImage.bmp")

    
    while True:
        
        MainLoop(ir0)

        firenum += 1
        


except KeyboardInterrupt:
    print 'KILL - NO FIRE ALL'
    ser.write(chr(254))#Switches Serial Off.
    ser.write(chr(29))
    ser.write(chr(254))
    ser.write(chr(29))
    ser.flushInput()
    ser.close()
    cv2.destroyAllWindows() 
    cv2.VideoCapture(0).release()
    sys.exit()
