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



time.sleep(30)
while(True):
#==================Modem
    try:
        byteOutput = subprocess.check_output(['nmcli','device','show'], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
        #nmcli device show
    except subprocess.CalledProcessError as e:
        print("Error cdc-wdm0", e.output)
        exit()

    lines = out.split('\n')

    if len(lines) < 5 :
        exit()

    foundModem = 0
    for idx in range(0, len(lines)):
        line = lines[idx]
        if 'tty' in line:
            print(line)
            
        if 'cdc-wdm' in line:
            print("found cdc-wdm")
            foundModem = 1

    if foundModem == 0:
        print("Not found cdc-wdm")
        print("restart NetworkManager ModemManager")
        os.popen("sudo systemctl restart NetworkManager ModemManager")
        time.sleep(60)


#==================Connection
    try:
        byteOutput = subprocess.check_output(['nmcli','device','show'], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
        #nmcli device show
    except subprocess.CalledProcessError as e:
        exit()
    lines = out.split('\n')
    if len(lines) < 5 :
        exit()
    foundConnection = 0
    for idx in range(0, len(lines)):
        line = lines[idx]
        if 'registered' in line:
            print(line)
        
        if 'unavailable' in line:
            print(line)
            #foundConnection = 30
        
        if 'enabled' in line:
            print(line)
            #foundConnection = 2
            #os.popen("sudo nmcli c up apn_tely")
            
        if 'connected' in line:
            print("found connected")
            #foundConnection = 1
            
        if 'apn_tely' in line:
            print("found apn_tely")
            foundConnection = 1

        if 'disconnected' in line:
            print("found disconnected")
            #foundConnection = 0

    if foundConnection == 30:
        print("Not found connected")
        print("Off wwan")
        os.popen("sudo nmcli r wwan off")
        time.sleep(2)
        print("On wwan")
        os.popen("sudo nmcli r wwan on")
        time.sleep(30)
        print("Connect")
        os.popen("sudo nmcli c up apn_tely")
        time.sleep(30)
        os.popen("sudo nmcli c mod apn_tely connection.autoconnect yes")

    if foundConnection == 31:
        try:
            driver = "Quectel"
            lsusb_out = Popen("lsusb | grep -i %s"%driver, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()
            bus = lsusb_out[1]
            device = lsusb_out[3][:-1]
            f = open("/dev/bus/usb/%s/%s"%(bus, device), 'w', os.O_WRONLY)
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
        except :
            print("failed to reset device:")
        os.popen("sudo systemctl restart NetworkManager ModemManager")

    if foundConnection == 0:
        print("Send reset device")
        try:
            ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=3.0 , rtscts=True, dsrdtr=True)
            ser.flushInput()
            ser.flushOutput()
            ser.write(str.encode('AT+QRST=1,0\r'))
            ser.close()
            print("device reset")
            time.sleep(30)
        except :
            print ("Serial Error")
        os.popen("sudo systemctl restart NetworkManager ModemManager")
#==================internet
    if internet_on() :
        print("internet OK")
        countInternet = 0
    else :
        countInternet += 1
        
    if countInternet > 2:
        countInternet = 0
        

    print("sleep")
    time.sleep(60)