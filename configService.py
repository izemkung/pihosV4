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

REMOTE_SERVER = "www.google.com"

def internet_on():
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(REMOTE_SERVER)
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False

def getModemInfo():
    res = {}
    out = ''
    try:
        byteOutput = subprocess.check_output(['mmcli','-m','0'], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
    except subprocess.CalledProcessError as e:
        print("Error in mmcli','-m','0'", e.output)
        return "error"

    lines = out.split('\n')

    if len(lines) < 5 :
         return "error"

    for idx in range(0, len(lines)):
        
        line = lines[idx]
        print(line)
            
        if '--------------------------' in line:
            cur_sys = None
            cur_subsys = None
            #print('None')
            continue

        if '|' not in line:
            continue

        if len(line.strip()) == 0:
            continue

        first_idx = line.find('|')
        if first_idx > 0:
            sys = re.search('([\w\d\s]+)', line[:first_idx]).group(1)
            sys = sys.strip()
            if sys is not '':
                cur_sys = sys
                res[cur_sys] = {}

            second_idx = line.find(':')
            if second_idx >= first_idx:
                subsys = re.search('([\w\d\s]+)', line[first_idx:second_idx]).group(1)
                subsys = subsys.strip()
                if subsys is not '':
                    cur_subsys = subsys
                    res[cur_sys][cur_subsys] = ''

                val = line[second_idx:].strip().strip(':').strip().strip('\'').strip()
                res[cur_sys][cur_subsys] = val

            elif second_idx == -1:
                val = line.strip().strip('\'').strip('|').strip()
                if val is not '':
                    res[cur_sys][cur_subsys] = res[cur_sys][cur_subsys] + ', ' + val
    return res


print ("Start configService")

if internet_on():
    print ( 'internet OK' )

modeminfo = getModemInfo()

if(modeminfo == "error"):
    print ('Air card Error') 

print (modeminfo['Hardware']['manufacturer'] + modeminfo['Hardware']['revision'] )
print (modeminfo['Hardware']['equipment id'] )

print (modeminfo['Status']['state'] ) # =searching(simOut) =failed(norfound) = connected(OK)
print (modeminfo['Status']['power state'] )
print (modeminfo['Status']['access tech'] )
print (modeminfo['Status']['signal quality'] )

print (modeminfo['3GPP']['imei'] )
print (modeminfo['3GPP']['operator id'] )
print (modeminfo['3GPP']['operator name'] )
print (modeminfo['3GPP']['registration'])


webConfig = requests.get('http://159.89.208.90:5000/config/' + modeminfo['3GPP']['imei'])

webConfig = webConfig.json()
del webConfig['_id']

mongoConn = pymongo.MongoClient()
db_pihos = mongoConn.pihos #test is my database
db_pihos_configs = db_pihos.configs #Here spam is my collection

newvalues = { "$set": webConfig}
print (newvalues)

db_pihos_configs.update_one({}, newvalues)

configs = list(db_pihos_configs.find())
print (configs)
mongoConn.close()

