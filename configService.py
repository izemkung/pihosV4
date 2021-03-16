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
from netifaces import interfaces, ifaddresses, AF_INET


REMOTE_SERVER = "www.google.com"
myconfig = ''

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

def getCPUInfo():
    res = {}
    out = ''
    try:
        byteOutput = subprocess.check_output(['cat','/proc/cpuinfo'], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
    except subprocess.CalledProcessError as e:
        print("Error cat /proc/cpuinfo", e.output)
        return "error"

    lines = out.split('\n')
    if len(lines) < 5 :
         return "error"

    for idx in range(0, len(lines)):
        
        line = lines[idx]
        first_idx = line.find(':')
        if first_idx > 0:
            sys = re.search('([\w\d\s]+)', line[:first_idx]).group(1)
            sys = sys.strip()
            if sys != '':
                cur_sys = sys
                res[cur_sys] = {}

            value_idx = line.find(':')
            if value_idx >= first_idx:
                val = line[value_idx:].strip().strip(':').strip().strip('\'').strip()
                res[cur_sys] = val

    try:
        byteOutput = subprocess.check_output(['vcgencmd','measure_temp' ], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
    except subprocess.CalledProcessError as e:
        print("Error measure_temp", e.output)
        return "error"

    first_idx = out.find('=') + 1


    res['Tepm'] = out[first_idx:].strip('\n')
    try:
        byteOutput = subprocess.check_output(['uptime'], timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
        first_idx = out.find('average:') + 9
        res['CPU'] = out[first_idx:].strip('\n')
    except:
        pass
    return res


def getConfig():
    global myconfig
    if internet_on() == False:
        return
   
    try:
        ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=0.1 , rtscts=True, dsrdtr=True)
        IMEI = get_Modem_info(ser,'AT+CGSN')[0]
        ser.close()
        print ( 'Read Configs ', IMEI )
        webConfig = requests.get('http://159.89.208.90:5000/config/' + IMEI)
        webConfig = webConfig.json()
    except:
        print ( 'Read Configs Error' )
        return

    del webConfig['_id']
    myconfig = webConfig
    #update config file
    my_file = open("/etc/hostapd/hostapd.conf")
    string_list = my_file.readlines()
    my_file.close()

    for idx in range(0, len(string_list)):
        line = string_list[idx]
        if 'AOC_' in line:
            first_idx = line.find('_') + 1
            currentID = line[first_idx:].strip('\n')
           
            if( currentID != webConfig['id'] ):
                print("Update Wifi SSID")
                string_list[idx] = 'ssid=AOC_' + webConfig['id'] + '\n'
                print(string_list[idx])
                my_file = open("/etc/hostapd/hostapd.conf", "w")
                new_file_contents = "".join(string_list)
                my_file.write(new_file_contents)
                my_file.close()
                os.popen("sudo service hostapd restart")
                print("Reboot hostapd Service")
                #reconnect camera
            else:
                print("Wifi SSID Ok.")

    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_configs = db_pihos.configs #Here spam is my collection

    
    #webConfig['mqtt'] =  "159.89.208.90"

    newvalues = { "$set": webConfig}
    print ('Write new configs ')
    print (newvalues)
    db_pihos_configs.update_one({}, newvalues)
    configs = list(db_pihos_configs.find())
    print ('Read current configs ')
    print (configs)
    mongoConn.close()

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

def networkStatus():
    global myconfig
    if internet_on() == False:
        return

    try:
        cpuinfo = getCPUInfo()
    except:
        return

    if(cpuinfo == "error"):
        print ('cpuinfo Error')

    #write config file
    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_status = db_pihos.status

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
    
    ser.close()

    #newvalues['apn'] = bearrerinfo['Properties']['apn']
    newvalues['model'] = cpuinfo['Model']
    newvalues['tepm'] = cpuinfo['Tepm']
    newvalues['cpu'] = cpuinfo['CPU']
    newvalues['id'] = myconfig['id']
    newvalues = { "$set": newvalues}
    db_pihos_status.update_one({}, newvalues)
    status = list(db_pihos_status.find())
    mongoConn.close()
    print ('Read current status ')
    print (status)

def sendStatusPack(msg,time):
    print ('Send Status Packet ')
    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_status = db_pihos.status #Here spam is my collection
    
    cur = db_pihos_status.find()
    status = list(cur)
    status[0]['msg'] = msg
    #status[0]['upTime'] = time
    byteOutput = subprocess.check_output(['uptime'], timeout=2)
    out = byteOutput.decode('UTF-8').rstrip()
    status[0]['upTime'] = out[1:out.find(',')]
    print (status[0])

    mongoConn.close()
    del status[0]['_id']
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post('http://159.89.208.90:5000/status/',data=json.dumps(status[0]), headers=headers)
  

def SendAlartFun(channel):
    global myconfig
    nti_url = myconfig['server'] + ":3020/api/notification"
    try:
        resp = requests.get(nti_url+'/?ambulance_id={0}&imei={2}'.format(myconfig[id], myconfig['sn']), timeout=3.001)
        print ('content     ' + resp.content) 
    except:
        print ('SendAlartFun Connection lost')


while(internet_on() == False):
    time.sleep(10)
print ("Start configService")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) ## Use board pin numbering
GPIO.setup(4, GPIO.IN) # Power
GPIO.setup(18, GPIO.IN) # Alart
GPIO.setup(17,GPIO.OUT) # LED Red
GPIO.add_event_detect(18, GPIO.RISING, callback=SendAlartFun, bouncetime=100)


lastTimeTask1 = time.time() + 600
lastTimeTask2 = time.time()
lastTimeTask3 = time.time() +20
timeStart = time.time()

getConfig()
sendStatusPack('Power on',0)

while(True):         

    currentTime = time.time()
    if currentTime > lastTimeTask1:
        lastTimeTask1 = currentTime + 600 #sec
        getConfig()

    if currentTime > lastTimeTask2:
        lastTimeTask2 = currentTime + 60 #sec
        networkStatus()

    if currentTime > lastTimeTask3:
        lastTimeTask3 = currentTime + 60
        sendStatusPack( 'online', (currentTime - timeStart)/60 )

    
