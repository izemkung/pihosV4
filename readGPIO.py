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
GPIO.setup(4, GPIO.IN) # Power
print("LED 3G GPIO(27)")
print(GPIO.input(27))

while True:
    if(GPIO.input(4) == 0):
        sendStatusPack( 'Power Off', (currentTime - timeStart)/60 )
        print("Pi Power Off Process!!")
        time.sleep(1)
        i = 0
        while( i < 20):
            i += 1
            time.sleep(0.2)
            GPIO.output(17,True)
            time.sleep(0.2)
            GPIO.output(17,False)
        os.system('sudo shutdown -h now')
        break

    time.sleep(1)

       