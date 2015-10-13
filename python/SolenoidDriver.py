# -*- coding: utf-8 -*-
"""
This script demonstrates how to communicate with the solenoid board (really
mosfet board). At the very least, it shows how to set up a socket connection to
the ethernet port.

The important part of this script is the gateRead() function. This (or 
something like it) will likely be what is implemented in the final code. There
may be better ways to do what is done here as this just a first attempt. This
should at least get you started on the right path.

For any questions about the transfer of information between machine and board,
refer to the documentation provided by Jeff.

Created on Mon Dec 15 16:24:24 2014

@author: Nick
"""

import  socket, time

def hexByte(ports):
    '''Accepts a tuple of integers 0-7 signifying the ports desired.
    Returns one byte to set the state of all ports simultaneously.
    
    Input:
        ports - Tuple of integers
        
    Output:
        cmd - Integer representation of unicode character.
    
    Example usage: binaryCode((0,4,6)) returns 81. User then sends chr(81)
        to the solenoid board which interprets the unicode character as an 
        8-bit binary switch, turning on solenoids 0, 4, and 6.
    
            bin(81) = '0b1010001' = 0 1 0 1 0 0 0 1
                                    7 6 5 4 3 2 1 0
                                      ^   ^       ^
    '''

    cmd = 0
    for port in ports:
        cmd |= 1<<port #shift a '1' onto cmd by 'port' bits via 'OR EQUALS'
    return cmd

def solenAct(ports,t=3):
    '''Activates defined ports for t (default 3) seconds. This function is
    mostly for debugging purposes. Returns the 7-byte command given to the
    board.
    '''
    source = 0xb3
    add = 0x01
    length = 0x07
    pl = 0x10
    s = hexByte(ports)
    cmdList = [source,add,length,pl,s]
    chksum = sum(x%8 for x in cmdList)
    cr = 0x0d
    cmdList += [chksum,cr]
    cmd = ''.join(map(chr,cmdList))
    solen.send(cmd)
    time.sleep(t)
    solen.send('\xb3\x01\x07\x10\x00\x0b\r')
    return cmd
    
def gateRead(ports=None, t=3):
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
        s = hexByte(ports) #Convert port info to hex byte
    else:
        s = 0x00    #Else fire no ports
    chksum += s%8   #Add MOD(solenoid byte,8)
    cmd = '\xb3\x01\x07\x10{0}{1}\x0d'.format(chr(s),chr(chksum)) #Compose command
    solen.send(cmd) #Sne dcommand to board
    if ports is not None:
        time.sleep(t)   #Fire for t seconds if ports were fired
        solen.send('\xb3\x01\x07\x10\x00\x0b\r') #Close ports
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
        return ir, uv
    except socket.timeout: #Catch a timeout error gracefully
        print('Timed out')
        pass
    

# Set TCP/IP port and time out. This is boilerplate setup for Windows machines
# Not sure exactly yet what this looks like for RaspPi (Linux), but should be similar.
solen = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
##solen = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
solen.settimeout(1.0)
#Try to connect to the board, else change the machine IP configuration settings
#to the required setup for the board to be able to communicate with it.
#This *should* work for any Windows machine (as long as your running Python as
#an administrator), but almost definitely will not work for the RaspPi. For
#linux, you will need to change the command you send the machine via os.system
try:
    solen.connect(("169.254.202.181",10001)) #Board address from documentation
#    solen.connect(("169.254.158.235",10002))
except:
    import os, ctypes, sys
    if not ctypes.windll.shell32.IsUserAnAdmin():
        sys.exit('You are not running Python as an administrator.\nPlease relaunch as an administrator.')
    os.system('netsh interface ip set address "Ethernet" static 169.254.210.189 255.255.0.0')
    solen.connect(("169.254.202.181",10001))

# Close the socket connection to the solenoid.
#solen.close()
