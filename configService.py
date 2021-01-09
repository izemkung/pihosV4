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

def getModemInfo(cmd):
    res = {}
    out = ''
    try:
        byteOutput = subprocess.check_output(cmd, timeout=2)
        out = byteOutput.decode('UTF-8').rstrip()
    except subprocess.CalledProcessError as e:
        print("Error in mmcli -m 0", e.output)
        return "error"

    lines = out.split('\n')

    if len(lines) < 5 :
         return "error"

    for idx in range(0, len(lines)):
        
        line = lines[idx]
        #print(line)
            
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
            if sys != '':
                cur_sys = sys
                res[cur_sys] = {}

            second_idx = line.find(':')
            if second_idx >= first_idx:
                subsys = re.search('([\w\d\s]+)', line[first_idx:second_idx]).group(1)
                subsys = subsys.strip()
                if subsys != '':
                    cur_subsys = subsys
                    res[cur_sys][cur_subsys] = ''

                val = line[second_idx:].strip().strip(':').strip().strip('\'').strip()
                res[cur_sys][cur_subsys] = val

            elif second_idx == -1:
                val = line.strip().strip('\'').strip('|').strip()
                if val != '':
                    res[cur_sys][cur_subsys] = res[cur_sys][cur_subsys] + ', ' + val
    return res

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

    print ( 'Read Configs' )
   
    modeminfo = getModemInfo(['mmcli','-m','0'])
    if(modeminfo == "error"):
        print ('Modem Error') 
        return
    
    try:
        webConfig = requests.get('http://159.89.208.90:5000/config/' + modeminfo['3GPP']['imei'])
        webConfig = webConfig.json()
    except:
        return

    del webConfig['_id']
    myconfig = webConfig
    #update config file
    my_file = open("/etc/hostapd/hostapd.conf")
    string_list = my_file.readlines()
    my_file.close()

    for idx in range(0, len(string_list)):
        line = string_list[idx]
        if 'PihosV4_' in line:
            first_idx = line.find('_') + 1
            currentID = line[first_idx:].strip('\n')
           
            if( currentID != webConfig['id'] ):
                print("Update SSID")
                string_list[idx] = 'ssid=PihosV4_' + webConfig['id'] + '\n'
                print(string_list[idx])
                my_file = open("/etc/hostapd/hostapd.conf", "w")
                new_file_contents = "".join(string_list)
                my_file.write(new_file_contents)
                my_file.close()
                os.popen("sudo service hostapd restart")
                print("Reboot hostapd Service")
                #reconnect camera
            else:
                print("SSID Ok.")

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
    
def networkStatus():
    global myconfig
    if internet_on() == False:
        return

    modeminfo = getModemInfo(['mmcli','-m','0'])
    siminfo = getModemInfo(['mmcli','-i','0'])
    bearrerinfo = getModemInfo(['mmcli','-b',modeminfo['Bearer']['dbus path'][38:].strip('\n')])
    cpuinfo = getCPUInfo()
    #print (cpuinfo)

    if(modeminfo == "error"):
        print ('Modem Error') 
    if(siminfo == "error"):
        print ('sim Error') 
    if(bearrerinfo == "error"):
        print ('bearrerinfo Error') 
    if(cpuinfo == "error"):
        print ('cpuinfo Error')

    #write config file
    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_status = db_pihos.status
    newvalues = {}
    newvalues['accessTech'] = modeminfo['Status']['access tech']
    newvalues['imei'] = modeminfo['Hardware']['equipment id']
    newvalues['modem'] = modeminfo['Hardware']['manufacturer'] +' ' + modeminfo['Hardware']['revision'] 
    newvalues['sinnalQuality'] = modeminfo['Status']['signal quality']
    newvalues['imsi'] = siminfo['Properties']['imsi']
    newvalues['iccid'] = siminfo['Properties']['iccid']
    newvalues['operator'] = modeminfo['3GPP']['operator name'] +' ' +siminfo['Properties']['operator name']
    newvalues['apn'] = bearrerinfo['Properties']['apn']
    newvalues['ip'] = bearrerinfo['IPv4 configuration']['address']
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
    print ('Read status ')
    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_status = db_pihos.status #Here spam is my collection
    
    cur = db_pihos_status.find()
    status = list(cur)
    status[0]['msg'] = msg
    #status[0]['upTime'] = time
    byteOutput = subprocess.check_output(['uptime'], timeout=2)
    out = byteOutput.decode('UTF-8').rstrip()
    status[0]['upTime'] = out[1:].strip('s,')
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
GPIO.setup(3, GPIO.IN) # Alart
GPIO.setup(17,GPIO.OUT) # LED Red
GPIO.add_event_detect(3, GPIO.RISING, callback=SendAlartFun, bouncetime=100)


lastTimeTask1 = time.time()
lastTimeTask2 = time.time()
lastTimeTask3 = time.time()
timeStart = time.time()

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

    if(GPIO.input(4) == 0):
        sendStatusPack( 'Off ', (currentTime - timeStart)/60 )
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
