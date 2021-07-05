import RPi.GPIO as GPIO ## Import GPIO library
import os
import time
import requests
import sys
import socket
import serial
import fcntl
import struct
import unittest
import subprocess
import inspect
import json
import re
import pymongo

USBDEVFS_RESET= 21780

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN)#3G
GPIO.setup(4, GPIO.IN)#Power


countInternet = 0
foundModem = 0
def internet_on():
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname("www.google.com")
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False

def ResetModem():
    print("ps internet: Send reset device ttyUSB2")
    try:
        ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=3.0 , rtscts=True, dsrdtr=True)
        ser.flushInput()
        ser.flushOutput()
        ser.write(str.encode('AT+QRST=1,0\r'))
        ser.close()
        print("ps internet:wait device start 30 sec ")
        time.sleep(3)
    except :
        print ("ps internet:Serial Error")
    print("ps internet: Ok")
    #os.popen("sudo systemctl restart NetworkManager ModemManager")
    time.sleep(60)



time.sleep(10)
while(True):
#==================internet=====================
    if internet_on() :
        print("ps internet: internet OK... sleep 30 sec.")
        countInternet = 0
    else :
        countInternet += 1
        
    if (countInternet > 2) and (GPIO.input(27) == 1):
        if(countInternet > 2):
            print("ps internet: internet Error")
        if(GPIO.input(27) == 1):
            print("ps internet: LED 3G Error")
        countInternet = 0
        #ResetModem()

    

        
    #print("ps internet: sleep")
    time.sleep(30)