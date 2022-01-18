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
from gps import *
import threading
from netifaces import interfaces, ifaddresses, AF_INET


REMOTE_SERVER = "www.google.com"
myconfig = ''
gpsd = None
threadingOut = False 

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    global threadingOut
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
      if(threadingOut):
        break

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

def get_Modem_info(ser,cmd):
    res = []
    lines = ''
    cmd = cmd + '\r\n'
   
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

    #print(res)
    return res

def getConfig():
    global myconfig
    if internet_on() == False:
        return
   
    IMEI = 'null'
    try:
        ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=0.1 , rtscts=True, dsrdtr=True)
        time.sleep(0.5)
        get_Modem_info(ser,'AT')
        get_Modem_info(ser,'ATE0')
        time.sleep(0.5)
        IMEI = get_Modem_info(ser,'AT+CGSN')[0]
        ser.close()
    except:
        print ( 'serial Error' )
        return

    if(len(IMEI) < 10):
        print ( 'IMEI error' )
        return

    print ( 'Read Configs ', IMEI )

    try:
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
           
            if( currentID != webConfig['sn'][-5:] ):
                print("Update Wifi SSID")
                string_list[idx] = 'ssid=AOC_' + webConfig['sn'][-5:] + '\n'
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
    old_configs = list(db_pihos_configs.find())
   
    #webConfig['mqtt'] =  "159.89.208.90"

    newvalues = { "$set": webConfig}
    print ('Write new configs ')
    print (newvalues)
    db_pihos_configs.update_one({}, newvalues)
    configs = list(db_pihos_configs.find())
    print ('Read current configs ')
    print (configs)
    mongoConn.close()

    if old_configs[0]['id'] != webConfig['id']:
        os.system('sudo pm2 restart all')

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
    ser.write(str.encode('AT\r'))
    time.sleep(0.5)
    ser.flushInput()
    ser.flushOutput()

    #SIM Info
    try:
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
    except:
        #LAN Info
        newvalues['operator'] = "LAN INT"
        addresses = [i['addr'] for i in ifaddresses('eth0').setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        newvalues['ip'] = addresses[0]

    ser.close()


    #newvalues['apn'] = bearrerinfo['Properties']['apn']
    newvalues['model'] = cpuinfo['Model']
    newvalues['tepm'] = cpuinfo['Tepm']
    newvalues['cpu'] = cpuinfo['CPU']
    newvalues['id'] = myconfig['id']
    newvalues['installLocation'] = myconfig['installLocation']
    newvalues['installDate'] = myconfig['installDate']
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
    byteOutput = subprocess.check_output(['uptime -s'], timeout=2)
    out = byteOutput.decode('UTF-8').rstrip()

    byteOutput = subprocess.check_output(['uptime -p'], timeout=2)
    out1 = byteOutput.decode('UTF-8').rstrip()

    status[0]['upTime'] = out +' ' + out1
    print (status[0])

    mongoConn.close()
    del status[0]['_id']
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post('http://159.89.208.90:5000/status/',data=json.dumps(status[0]), headers=headers)
  

def SendCreashFun():
    global myconfig
    global gpsd
    #print ('SendCreashFun')
    nti_url = myconfig['server'] + ":3020/api/notification"
    try:
        nti_url = nti_url+'?ambulance_id={0}&tracking_latitude={1:.6f}&tracking_longitude={2:.6f}&tracking_speed={3:.2f}&tracking_heading={4}'.format(myconfig['id'],gpsd.fix.latitude,gpsd.fix.longitude,gpsd.fix.speed,gpsd.fix.track)
        #print(nti_url)
        resp = requests.get(nti_url,timeout=(2.05, 5))       
        print ('SendCreashFun     '+ str(resp.status_code)) 
    except:
        print ('SendCreashFun Connection lost')


while(internet_on() == False):
    time.sleep(10)
print ("Start configService")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) ## Use board pin numbering
GPIO.setup(4, GPIO.IN) # Power
GPIO.setup(18, GPIO.IN) # Alart
GPIO.setup(17,GPIO.OUT) # LED Red
GPIO.add_event_detect(18, GPIO.RISING, callback=SendCreashFun, bouncetime=100)


lastTimeTask1 = time.time() + 600
lastTimeTask2 = time.time()
lastTimeTask3 = time.time() +20
timeStart = time.time()

getConfig()
sendStatusPack('Power on',0)
gpsp = GpsPoller()
gpsp.start()

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

    time.sleep(2)


threadingOut = True
gpsp.running = False
print ("Configs.\nExiting.")