import RPi.GPIO as GPIO ## Import GPIO library
import ConfigParser
import os
import time
import requests
import sys
import socket
import serial
import fcntl
import struct

REMOTE_SERVER = "www.google.com"
flagDetectHW_GPS = False
VERSION_FW = 34
version_config = "34"

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

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def SendAlartFun(channel):
    try:
        resp = requests.get(nti_url+'?ambulance_id={0}'.format(id), timeout=3.001)
        print ('content     ' + resp.content) 
    except:
        print 'SendAlartFun Connection lost'

def SendStatusFun(message):
    try:
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.1)
        ser.write('AT+QCCID\r')
        time.sleep(2)

        for num in range(0, 10):
            bufsid = ser.readline()
            if len(bufsid) >= 20 :
                break

        replacements = (',', '\r', '\n', '?')
        for r in replacements:
            bufsid = bufsid.replace(r, ' ')
        SID = bufsid.split(" ")
        #print SID
        #SID = CID[1]
        
        ser.write('AT+GSN\r')
        time.sleep(1)
        for num in range(0, 10):
            bufemi = ser.readline()
            if len(bufemi) >= 10 :
                break

        replacements = (',', '\r', '\n', '?')
        for r in replacements:
            bufemi = bufemi.replace(r, ' ')
        IMEI = bufemi.split(" ")
        #print IMEI
        #IMEI = emi[0]
        sidOk = True
        
        #print id
        ip = get_ip_address('ppp0') 
        #print ip
        #print SID
        #print IMEI
        api = nti_url.split("/")
        #print api[2]

        if len(SID[1]) <= 13:
            return False

        if flagDetectHW_GPS == True:
            api[2] += '_HW_35_'
        else:
            api[2] += '_UC_35_'
        api[2] += version_config
        
        resp = requests.get('http://188.166.197.107:8001?id={0}&ip={1}&sid={2}&imei={3}&api={4}&msg={5}'.format(id,ip,SID[1],IMEI[0],api[2],message), timeout=3.001)
        print ('http://188.166.197.107:8001?id={0}&ip={1}&sid={2}&imei={3}&api={4}&msg={5}'.format(id,ip,SID[1],IMEI[0],api[2],message))
        print ('content     ' + resp.content) 
        return True
    except:
        print 'SendStatusFun Connection lost'
    return False


        
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


print "Start GPIO"

#=========================Ennable UC20 GPS
time.sleep(5)
try:
    ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=3.0 , rtscts=True, dsrdtr=True)
    ser.flushInput()
    ser.flushOutput()
    ser.write('AT+GSN\r')

    for num in range(0, 10):
        bufemi = ser.readline()
        if len(bufemi) >= 10 :
            break
    replacements = (',', '\r', '\n', '?')
    for r in replacements:
        bufemi = bufemi.replace(r, ' ')
    IMEI = bufemi.split(" ")
    print IMEI[0]
    time.sleep(1)
    ser.write('AT+QGPS=1\r')
    ser.write('ATE0\r')
    

except:
    print "Serial Error"
    time.sleep(20)
    os.system('sudo reboot')
time.sleep(1)

#=========================Detect HW GPS
GPSPortUC20 = '/dev/ttyUSB1'
GPSPortHW =  '/dev/ttyAMA0'


try:
  os.system('sudo chmod +x /home/pi/pihos/connect.sh')
  os.system('sudo timedatectl set-ntp True')

  os.system('sudo systemctl stop gpsd.socket')
  os.system('sudo systemctl disable gpsd.socket')

  os.system('sudo systemctl stop gpsd.socket')
  os.system('sudo systemctl disable gpsd.socket')
except :
  print "Stop gpsd Error"

time.sleep(2)
#==============================HW Serial GPS Detection==============================
try:
    serDetec = serial.Serial(GPSPortHW, 9600 , timeout=1.0 , rtscts=True, dsrdtr=True)
    serDetec.flushInput()
    serDetec.flushOutput()
    time.sleep(1)
    for num in range(0, 20):
        #time.sleep(0.5)
        bufemi = serDetec.readline()
        print bufemi
        if bufemi[0] == '$' and bufemi[1] == 'G':
            flagDetectHW_GPS = True
            print "HW GPS Detect"
            break
    serDetec.close()
except:
    print "Open Serial HW Error"
    #time.sleep(10)
    #os.system('sudo reboot')

try:
  if flagDetectHW_GPS == True:
    print "gpsd > GPS HW"
    os.system('sudo gpsd {0} -F /var/run/gpsd.sock'.format(GPSPortHW))
  else:
    print "gpsd > GPS UC20"
    os.system('sudo gpsd {0} -F /var/run/gpsd.sock'.format(GPSPortUC20))
  
  time.sleep(1)
  os.system('sudo systemctl enable gpsd.socket')
  os.system('sudo systemctl start gpsd.socket')

  os.system('sudo systemctl enable gpsd.socket')
  os.system('sudo systemctl start gpsd.socket')
except :
  print "Init gpsd Error"



#sudo gpsd /dev/ttyUSB1 -F /var/run/gpsd.sock
#input2 = 0
#for num in range(0, 4):
#    port = '/dev/ttyUSB{0}'.format(num)
#    try:
#        ser = serial.Serial(port, 115200, timeout=.5)
#        input = ser.inWaiting()
#        print('Checking {0} Data In {1}'.format(port,input))
#        time.sleep(5)
#        input = ser.inWaiting()
#    except:
#        print('Port {0} busy'.format(port))

#    try:
#        input2 = 0
#        for count in range(0, 10):
#            inputS = ser.readline()
#            input2 += len(inputS)
#            print(inputS)
#        ser.close()
#    except:
#        print('Port {0} Except'.format(port))
#    print('Checked {0} Data In {1} DataS {2}'.format(port,input,input2))
#    if(input > 200) or (input2 > 100):
#        print('{0} Ok!!!'.format(port))
#        GPSPortUC20 = port
#        break
#time.sleep(10)
#os.system('clear') #clear the terminal (optional)

try:
    resp = requests.get('http://188.166.197.107/Config_API.php?IMEI=861075028784957')
    print resp.json()['API_NTI']
except :
  print "Get config error"
#{u'VERSION': u'72b1d9e5ef932f91e17b603f0cc0492cafa4a5db', u'TIME_PIC': u'0', u'CRASH_GAIN': u'10', u'REPO': u'pihos2', u'NUM': u'1',
# u'API_PIC': u'http://safetyam.tely360.com/api/upload.php', u'TIME_GPS': u'1', u'IMEI': u'861075028784957',  
# u'API_NTI': u'http://safetyam.tely360.com/api/notification.php', u'ID': u'99', u'API_GPS': u'http://safetyam.tely360.com/api/tracking.php', u'TIME_VDO': u'10'}
#id: 99
#timevdo: 10
#timepic: 1
#gps_api: http://safetyam.tely360.com/api/tracking.php
#pic_api: http://safetyam.tely360.com/api/upload.php
#nti_api: http://safetyam.tely360.com/api/notification.php

#if os.path.exists("config.ini") == False  :
#print("local config.ini error")
#print("load config.ini")
#if internet_on() == True :
#    resp = requests.get('http://188.166.197.107/Config_API.php?IMEI={0}'.format(IMEI[0]))
#    if os.path.exists("config.ini") == False  :
#        os.system('sudo touch /home/pi/config.ini')
#    with open("/home/pi/config.ini", "r+") as f:
#        f.seek(0) # rewind
#        f.write("[Profile]")
#        f.write("\r\nid : " + resp.json()['ID'])
#        f.write("\r\ntimevdo : " + resp.json()['TIME_VDO'])
#        f.write("\r\ntimepic : " + resp.json()['TIME_PIC'])
#        f.write("\r\ngps_api : " + resp.json()['API_GPS'])
#        f.write("\r\nnti_api : " + resp.json()['API_NTI'])
#        f.write("\r\pic_api : " + resp.json()['API_PIC'])
#        f.close()
#else: 
    #print("load config.ini internet Error")
'''       
if os.path.exists("/home/pi/usb/config.ini") == False:
    print("usb config.ini error")
    os.system('sudo mount /dev/sda1 /home/pi/usb/')
    exit()
else:
    if os.path.exists("/home/pi/config.ini") == True:
        os.system('sudo rm -rf config.ini')
    os.system('sudo mv /home/pi/usb/config.ini /home/pi/config.ini')
'''
#if os.path.exists("/home/pi/usb/pic") == True:
#    print("Delete Pic Foder!!!")
    #os.system('sudo mount /dev/sda1 /mnt/usbdrive')
#    os.system('sudo rm -rf /home/pi/usb/pic')
#    os.system('sudo mkdir /home/pi/usb/pic')
 #   os.system('sudo mkdir /home/pi/usb/pic/ch0')
#    os.system('sudo mkdir /home/pi/usb/pic/ch1')

#if os.path.exists("/home/pi/usb/vdo") == True:
 #   print("Delete Vdo Foder!!!")
    #os.system('sudo mount /dev/sda1 /mnt/usbdrive')
 #  os.system('sudo rm -rf /home/pi/usb/vdo')
  #  os.system('sudo mkdir /home/pi/usb/vdo')
 #   os.system('sudo mkdir /home/pi/usb/vdo/ch0')
  #  os.system('sudo mkdir /home/pi/usb/vdo/ch1')
    
       
Config = ConfigParser.ConfigParser()
Config.read('/home/pi/config.ini')

id =  ConfigSectionMap('Profile')['id']
print id
timevdo = ConfigSectionMap('Profile')['timevdo']
print timevdo
timepic = ConfigSectionMap('Profile')['timepic']
print timepic
nti_url = ConfigSectionMap('Profile')['nti_api']
print nti_url
try:
  version_config = ConfigSectionMap('Profile')['version']
except:
  version_config = "35"
  print("exception version")
print  'version > ',version_config

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) ## Use board pin numbering
GPIO.setup(3, GPIO.IN) # Alaet
GPIO.setup(4, GPIO.IN) # Power

GPIO.add_event_detect(3, GPIO.RISING, callback=SendAlartFun, bouncetime=100)

sendStart = False

current_time = time.time()
timeout2 = time.time()
timeStart = time.time()
timeout = time.time() + 60
while True:
    time.sleep(2)
    current_time = time.time()
#I/O Power on
    if sendStart == False  :
        if internet_on() == True :  
            if(SendStatusFun('Power Start') == True):
                sendStart = True
                print sendStart

#I/O Power off
    if(GPIO.input(4) == 0):
        print('Power Off')
        SendStatusFun('Power Off {0:.1f} Min'.format((current_time - timeStart)/60))
        time.sleep(20)
        os.system('sudo shutdown -h now')
        break

#On line status
    if time.time() > timeout2:
        print "Sent Online Status" 
        SendStatusFun('On {0:.1f} Min'.format((current_time - timeStart)/60))
        timeout2 = time.time() + 600

#Ennable GPS
    if time.time() > timeout:
        timeout = time.time() + 60
        ser.write('ATE0\r')
        ser.write('AT+QGPS=1\r')
        for num in range(0, 5):
            bufemi = ser.readline()
        print "Set Starting GPS"  

ser.close()
GPIO.cleanup()