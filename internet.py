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

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN)#3G

countInternet = 0
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

while(True):

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

    for idx in range(0, len(lines)):
        line = lines[idx]
        if 'tty' in line:
            print(line)
            os.popen("sudo systemctl restart NetworkManager ModemManager")
            print("restart NetworkManager ModemManager")
        if 'cdc-wdm' in line:
            print("found cdc-wdm")
            if internet_on() :
                print("internet OK")
                countInternet = 0
            else :
                countInternet += 1
                if countInternet > 2:
                    os.popen("sudo systemctl restart NetworkManager ModemManager")
                    print("restart NetworkManager ModemManager")
    print("sleep")
    time.sleep(60)