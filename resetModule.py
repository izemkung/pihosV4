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
print("device reset NetworkManager")
