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
#Camera I/O
GPIO.setup(8, GPIO.OUT)
GPIO.setup(9, GPIO.OUT)
GPIO.setup(10, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)


#print("LED 3G GPIO(27)")
#print(GPIO.input(27))

GPIO.output(8,False)
GPIO.output(9,False)
GPIO.output(10,False)
GPIO.output(11,False)
time.sleep(10)
print("Camera start!!!")
while True:
    
    if(GPIO.input(4) == 1):
        GPIO.output(8,True)
        GPIO.output(9,True)
        GPIO.output(10,True)
        GPIO.output(11,True)
    else:
        GPIO.output(8,False)
        GPIO.output(9,False)
        GPIO.output(10,False)
        GPIO.output(11,False)

    time.sleep(10)

       