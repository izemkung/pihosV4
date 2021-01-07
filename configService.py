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
    res['CPU'] = str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip())
    return res




print ("Start configService")

if internet_on():
    print ( 'internet OK' )

    modeminfo = getModemInfo(['mmcli','-m','0'])
    siminfo = getModemInfo(['mmcli','-i','0'])
    bearrerinfo = getModemInfo(['mmcli','-b','0'])
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

    '''
    try:
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

        print (siminfo['Properties']['imsi'])
        print (siminfo['Properties']['iccid'])
        print (siminfo['Properties']['operator name'])
    except:
            pass
    '''

    webConfig = requests.get('http://159.89.208.90:5000/config/' + modeminfo['3GPP']['imei'])
    webConfig = webConfig.json()
    del webConfig['_id']

    #update config file
    my_file = open("/etc/hostapd/hostapd.conf")
    string_list = my_file.readlines()
    my_file.close()

    #webConfig['id'] = '98'
    #print(string_list)

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
                

    #write config file
    mongoConn = pymongo.MongoClient()
    db_pihos = mongoConn.pihos #test is my database
    db_pihos_configs = db_pihos.configs #Here spam is my collection
    db_pihos_status = db_pihos.status

    newvalues = { "$set": webConfig}
    print ('Load configs ')
    print (newvalues)

    db_pihos_configs.update_one({}, newvalues)

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

    newvalues = { "$set": newvalues}
    db_pihos_status.update_one({}, newvalues)


    configs = list(db_pihos_configs.find())
    print ('Read current configs ')
    print (configs)
    configs = list(db_pihos_status.find())
    print ('Read current status ')
    print (configs)
    mongoConn.close()



