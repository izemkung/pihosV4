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


from netifaces import interfaces, ifaddresses, AF_INET


def get_Modem_info(ser,cmd):
    res = []
    lines = ''
    cmd = cmd + '\r'
    ser.flushInput()
    ser.flushOutput()
    ser.write(str.encode(cmd))
    #time.sleep(0.5)
    lines = ser.readlines()
    

    if lines == '':  # timeout
        print("timeout")

    for idx in range(0, len(lines)):
        line = lines[idx].decode("utf-8") 
        if(line != '\r\n'):
            res.append(line.replace("\r\n", ""))

    return res

ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=0.1 , rtscts=True, dsrdtr=True)

newvalues = {}

accessTech = get_Modem_info(ser,'AT+QNWINFO')[0].split(',')
newvalues['accessTech'] = accessTech[0][accessTech[0].find('"')+1:-1]  +' ' +accessTech[2].strip('"')
modem = get_Modem_info(ser,'ATI')
newvalues['modem'] = modem[0] +' '+modem[1]+' '+modem[2][modem[2].find(' '):]
sinnal = get_Modem_info(ser,'AT+CSQ')
newvalues['sinnalQuality'] = sinnal[0][sinnal[0].find(' '):].strip()
newvalues['imei'] = get_Modem_info(ser,'AT+CGSN')[0]
newvalues['imsi'] = get_Modem_info(ser,'AT+CIMI')[0]
ccid = get_Modem_info(ser,'AT+QCCID')
newvalues['iccid'] = ccid[0][ccid[0].find(' '):].strip()
operator = get_Modem_info(ser,'AT+QSPN')[0].split(',')
newvalues['operator'] = operator[2].strip('"') +' '+ operator[1].strip('"')
addresses = [i['addr'] for i in ifaddresses('wwan0').setdefault(AF_INET, [{'addr':'No IP addr'}] )]
newvalues['ip'] = addresses[0]

print (newvalues)

print(get_Modem_info(ser,'ATI'))
print(get_Modem_info(ser,'AT+CGSN'))
print(get_Modem_info(ser,'AT+CIMI'))
print(get_Modem_info(ser,'AT+QCCID'))
print(get_Modem_info(ser,'AT+QSPN'))
print(get_Modem_info(ser,'AT+CSQ'))
print(get_Modem_info(ser,'AT+QNWINFO'))

ser.close()

time.sleep(3)

#os.popen("sudo systemctl restart NetworkManager ModemManager")

