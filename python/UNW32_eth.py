#This code written using Python 2.7.5 for WindowsXP

# Import all of the modules needed to use serial, do image processing, etc.
import ImageChops, ImageDraw, socket, time, bisect, scipy, threading, cv2
from VideoCapture import Device
from datetime import datetime
import PIL.Image
import numpy as np
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters

# Some helpful functions to make the code easier to read, follow, and modify
def gateRead(solen,ports=None, t=3):
    '''Activates ports for t (default 3) seconds. If not given any arguments,
    the function return value is the value of the ir bytes (2) and UVtron byte.
    NOTE: I haven't gotten to interpreting the return bytes yet. I was working
    on that when I fried the board. 
    
    Input:
        ports - Tuple of integers representing which ports to fire.
        t - Time (in seconds) of fire time
        
    Output:
        ir - ADC IR analog value from board. 12-bit float
        uv - Digital UVTron value. '1' means a flame is detected.
    '''
    chksum = 11     # Sum(MOD(byte,8)) for first four bytes which never change
    if ports is not None:
        s = portMap(ports) #Convert port info to hex byte
    else:
        s = 0x00    #Else fire no ports
    chksum += s%8   #Add MOD(solenoid byte,8)
    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum)) #Compose command
    solen.send(cmd) #Sne dcommand to board
    if ports is not None:
        time.sleep(t)   #Fire for t seconds if ports were fired
        solen.send('\xb3\x01\x07\x10\x00\x0b\r') #Close ports
    return 1
    try:
        #Get the return values from the board. Essentially, iterate the command
        #to recieve 1 byte from the board until a carriage return (stop bit) is
        #received. Then store all values in a list named "ret"
        ret = tuple(iter(lambda: solen.recv(1),'\r'))
        ret = map(ord,ret)  #Convert bytestrings in ret to integers
        #The analog IR value is split between two bytes, with the bits 12-16 
        #always set to 0. We shift the most significant byte 8 bits and join it
        #with the least significant bit to construct our value
        ir = ret[4]<<8 | ret[5]
        uv = ret[6]
        return ir > 2048 and uv
    except socket.timeout: #Catch a timeout error gracefully
        print('Timed out')
        pass
    

#def serialQuery(lock):
#    global Gate, Override
#    while True:
#        gateCheck = 3
#        lock.acquire()
#        ser.flushInput()
#        try:
#            while gateCheck:
#                ser.write(chr(254))
#                ser.write(chr(152))
#                try:
#                    Gate = ord(ser.read(10))
#                except TypeError:
#                    Gate = 255
#                    ser.flushInput()
#                lock.release()
#                gateCheck -= 1
#            lock.acquire()
#            ser.write(chr(254))
#            ser.write(chr(153))
#            try:
#                Override = ord(ser.read(10))
#            except TypeError:
#                Override = 255
#                ser.flushInput()
#            print Gate,Override
#        except:
#            lock.release()
#            break
#        lock.release()

def gateCheck(solen,lock,ports=None,t=3):
    global Gate, Override
    Override = 0
    while True:
#        lock.acquire()
#        Gate = gateRead(solen,ports,t)
        Gate = 1
#        lock.release()
        
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
    
    
def portMap(ports):
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

    cmd = 0
    for port in ports:
        cmd |= 1<<port #shift a '1' onto cmd by 'port' bits via 'OR EQUALS'
    return cmd

def portFire(dat, Dist1, Dist2, fireDict, t2, solen, lock):
    '''FUNCTION IS DEPRECATED. IT IS KEPT HERE ONLY FOR THE DISTANCE LOGIC.
    Sends serial command to board to fire selected solenoids. The option
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
## The following lines are not functional, but also not used because this function is not used.
    t3 = time.clock();
    lock.acquire()
    solen.send(chr(portMap(fireDict[dat])))
    lock.release()
    print 'Location: ' + str(dat) + ', Firing: ' + ' & '.join(map(str, fireDict[dat]))
    t4=time.clock();
    
    time.sleep(3) #Duration of Burst, in seconds
    print 'Speed of detect-to-activation start was:', t3-t2
    print 'Speed of detect-to-activation end was:', t4-t2

def main(ir0,lock):
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
    xsplit = xsize / float(xgrid)
    ysplit = ysize / float(ygrid)
    xdivs = range(0, xsize + int(xsplit), int(xsplit))
    ydivs = range(0, ysize + int(ysplit), int(ysplit))
    
    while True:
##            ser.write(chr(254))
##            ser.write(chr(150))
##            Dist1 = ser.read(10)
##            ser.write(chr(254))
##            ser.write(chr(151))
##            Dist2 = ser.read(10)
##            Dist1 = ord(Dist1)
##            Dist2 = ord(Dist2)
#        Dist1 = 0
#        Dist2 = 0
        if not 'Gate' in globals():
            continue
        if not Gate: # If "Gate" is not open
            if 'ir1' in locals(): # if there exists a variable 'ir1' (i.e,
                ir0 = ir1           # it is not on the first iteration)
            ir1 = cam0.getImage()   # Always take a new picture for reference
            
            if not 'Override' in globals():
                continue
            if Override:      # If "Override" has been triggered
                lock.acquire()
                print 'OVERRIDE - FIRE ALL'
#                ser.write(chr(254))
#                ser.write(chr(30))  # Dump all ports
#                time.sleep(1)
#                ser.write(chr(254)) # Closes all ports.
#                ser.write(chr(29))
#                ser.write(chr(254))
#                ser.write(chr(29))
#                ser.flushInput()        
                solen.send('\xb3\x01\x07\x10\x80\x0b\r') #Fire all ports
                lock.release()
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
            Read = gateRead(solen,dat,lock)
            if (Read != ""):
                    xarea = xzone*(xsize/float(xgrid)) #Calculates Rectangle
                    yarea = yzone*(ysize/float(ygrid))
                    lock.acquire()                    
                    solen.send('\xb3\x01\x07\x10\x00\x0b\r') #Close ports, just in case
                    lock.release()
                    draw = ImageDraw.Draw(ira)#Initilizes Draw Class
                    draw.rectangle((xarea,yarea,xarea+xsplit,yarea+ysplit),outline=128) #Highlights Trigger Zone
                    fo = '-'.join(map(str, datetime.now().timetuple()[:6]))
                    ira.save('fire'+fo+'.bmp')
##                    del ir0, ir1, ira
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
    portcombos = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (1, 2), (2, 3), (3, 4), (3, 4)]
    xgrid = 9
    ygrid = 1
    grid = [(x,y) for y in range(ygrid) for x in range(xgrid)] # xgridXygrid grid locations
    fireDict = dict(zip(grid,portcombos)) # Hash grid locations to ports
    
    print 'Startup time:', t0


    # Set TCP/IP port and time out. This is boilerplate setup for Windows machines
    # Not sure exactly yet what this looks like for RaspPi (Linux), but should be similar.
#    solen = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    solen = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # Could possibly be better (faster?) as a UDP connection in which case:
#    solen = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # UDP connections are more prone to packet drops, but we might be okay.
    solen.settimeout(0)
    #Try to connect to the board, else change the machine IP configuration settings
    #to the required setup for the board to be able to communicate with it.
    #This *should* work for any Windows machine (as long as your running Python as
    #an administrator), but almost definitely will not work for the RaspPi. For
    #linux, you will need to change the command you send the machine via os.system
    try:
        solen.connect(("169.254.202.181",10001)) #Board address from documentation
    except:
        import os, ctypes, sys
        if not ctypes.windll.shell32.IsUserAnAdmin():
            sys.exit('You are not running Python as an administrator.\nPlease relaunch as an administrator.')
        os.system('netsh interface ip set address "Ethernet" static 169.254.210.189 255.255.0.0')
        solen.connect(("169.254.202.181",10001))

##    rgbavg = 100
##    counter = 1
##
##    cap = cv2.VideoCapture(0)
##    cap.set(3,160)
##    cap.set(4,120)
##    
##    ## To Activate Automatic Calibration, Un/Comment-out the following section
##    ## ---------------Start of Calibration-------------------
##    
##    cap.set(6,30)
##    cap.set(14,20)
##
##    tog1 = 2
##    tog2 = 2
##    bright = 70
##    con = 70
##    cap.set(10,bright)
##    cap.set(11,con)
##    bvar = 0
##    cvar = 0
##    gmax = 100
##    scord = 3
##    mcord = 3
##
##    while ( rgbavg > 12) or (gmax > 150):
##        
##        if not tog1%2:
##            if not tog2%2:
##                bvar += 5
##                cap.set(10,bright-bvar)
##            else:
##                bvar += 5
##                cap.set(10,bright-bvar)
##        else:
##            if not tog2%2:
##                cvar += 5
##                cap.set(11,con+cvar)
##                tog2 += 1
##            else:
##                cvar += 5
##                cap.set(11,con+cvar)
##                tog2 += 1
##
##        tog1 += 1
##        print counter
##        counter += 1
##        if counter > 3:
##            cap.set(10,20)
##            cap.set(11,70)
##            break
##        brightP = cap.get(10)
##        conP = cap.get(11)
##        print brightP, 'Brightness'
##        print conP, 'Contrast'
##
##        ret, img = cap.read()
##        ret, img = cap.read()
##        ret, img = cap.read()
##
##        cv2.imwrite("irCalib.bmp", img)
##
        ir0 = PIL.Image.open("irCalib.bmp")
##
##        rtot = 0
##        gtot = 0
##        btot = 0
##        gmax = 0
##
##        xsize = int(cap.get(3))
##        ysize = int(cap.get(4))
##        for s in range(0,xsize/2): #These Four Lines Control Skips
##            s=s*2                  # Change the 3 to how ever you want to skip
##            for m in range(0,ysize/2): #plus 1
##                    m=m*2 #
##                    pix = ir0.load()
##                    r,g,b = pix[s,m]
##                    rtot += r
##                    gtot += g
##                    btot += b
##                    if g > gmax:
##                        gmax = g
##                        scord=s
##                        mcord=m
##
##        ravg = rtot/(xsize*ysize/4)/2.55 #Skips here, too
##        gavg = gtot/(xsize*ysize/4)/2.55
##        bavg = btot/(xsize*ysize/4)/2.55    
##        rgbavg = (ravg + gavg + bavg)/3
##
##        if (0 < scord < xsize) and (0 < mcord < ysize):
##            r,g1,b = pix[scord, mcord]
##            r,g2,b = pix[scord+1, mcord]
##            r,g3,b = pix[scord, mcord+1]
##            r,g4,b = pix[scord-1, mcord]
##            r,g5,b = pix[scord, mcord-1]
##            gmaxarea = (g1+g2+g3+g4+g5)/5
##        else:
##            gmaxarea = gmax
##            print 'safeguard active'
##        
##        print rgbavg, 'percent white'
##        print gmaxarea, 'g max value'
##        del ir0, s, m, xsize, ysize, pix, r, g, b, rtot, gtot, btot, ravg, gavg, bavg
##
##    ## --------------End of Calibration-------------------
##    
##    ret, img = cap.read()
##    ret, img = cap.read()
##    cv2.imwrite("irFirstImage.bmp", img)
##
##    cv2.destroyAllWindows() 
##    cv2.VideoCapture(0).release()
##
##    t1=time.clock();
##    print 'time of calibration:', t1
##
##    cam0.setResolution(160,120)
    ir0 = PIL.Image.open("irFirstImage.bmp")
    
##        while True:
    lock = threading.Lock()
    t1 = threading.Thread(target = gateCheck,args = (solen,lock,))
    t1.daemon = True
    t1.start()
    t2 = threading.Thread(target = main, args = (ir0,lock,))
    t2.daemon = True
    t2.start()
    while True:
        if not t2.isAlive():
            t2 = threading.Thread(target = main, args = (ir0,lock,))
            t2.daemon = True
            t2.start()
            

    firenum += 1
    


except KeyboardInterrupt:
    print 'KILL - NO FIRE ALL'
    solen.send('\xb3\x01\x07\x10\x00\x0b\r')
    solen.close()
#    cv2.destroyAllWindows() 
#    cv2.VideoCapture(0).release()
#    sys.exit()
