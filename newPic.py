import os
import glob
import cv2
import cv
import datetime
import base64
import requests
import urllib2
import httplib
import time
#import RPi.GPIO as GPIO ## Import GPIO library
import ConfigParser
import hashlib

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

if os.path.exists("/home/pi/usb/config.ini") == False:
    print("config.ini error")
    os.system('sudo mount /dev/sda1 /home/pi/usb/')
    #exit()


os.system('sudo mount -o rw,remount /dev/sda1')
os.system('sudo rm /home/pi/usb/pic/ch0/*.jpg') 
os.system('sudo mount -o rw,remount /dev/sda1') 
os.system('sudo rm /home/pi/usb/pic/ch1/*.jpg')

try:
    os.system('sudo mount /dev/sda1 /home/pi/usb/')
except:
    print('Error mount')

if os.path.exists("/home/pi/usb/config.ini") == False:
    print("usb config.ini error")
    os.system('sudo mount /dev/sda1 /home/pi/usb/')
    #exit()
else:
    if os.path.exists("/home/pi/config.ini") == True:
        os.system('sudo rm -rf config.ini')
    os.system('sudo cp /home/pi/usb/config.ini /home/pi/config.ini')

time.sleep(2)
Config = ConfigParser.ConfigParser()
Config.read('/home/pi/config.ini')

id =  ConfigSectionMap('Profile')['id']
timevdo = ConfigSectionMap('Profile')['timevdo']
timepic = ConfigSectionMap('Profile')['timepic']
gps_url = ConfigSectionMap('Profile')['gps_api']
pic_url = ConfigSectionMap('Profile')['pic_api']

OldPic0 = ''
OldPic1 = ''
countError = 0
countPic = 0
countNoNewpic = 0
connectionError = 0

#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM) ## Use board pin numbering
#GPIO.setup(17, GPIO.OUT)#Rec
#GPIO.setup(27, GPIO.OUT)#3G
BLOCKSIZE = 65536

timeout = time.time() + 600  
while True:
    

    hasher1 = hashlib.md5()
    hasher2 = hashlib.md5()
    with open('/home/pi/config.ini', 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher1.update(buf)
            buf = afile.read(BLOCKSIZE)
    #print(hasher1.hexdigest())

    with open('/home/pi/usb/config.ini', 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher2.update(buf)
            buf = afile.read(BLOCKSIZE)
    #print(hasher2.hexdigest())

    info1 = os.stat('/home/pi/config.ini')
    info2 = os.stat('/home/pi/usb/config.ini')
    #print info1.st_mtime
    #print info2.st_mtime
    #fileConfig1 = max(glob.iglob('/home/pi/config.ini'), key=os.path.getctime)
    #fileConfig2 = max(glob.iglob('/home/pi/usb/config.ini'), key=os.path.getctime)

    if hasher1.hexdigest() !=  hasher2.hexdigest():
        os.system('sudo rm -rf /home/pi/config.ini')
        os.system('sudo cp /home/pi/usb/config.ini /home/pi/config.ini')
        #os.system('sudo rm -rf /home/pi/usb/config.ini')
        #os.system('sudo cp /home/pi/config.ini /home/pi/usb/config.ini')
        print "New File Config"
    else :
        print "File Config Ok"
    time.sleep(60)
    #GPIO.output(17,False)
    if time.time() > timeout:
        print "Timeout"
        break

'''
    timeout = time.time() + 10

    newpic1 = max(glob.iglob('/home/pi/usb/pic/ch1/*.[Jj][Pp][Gg]'), key=os.path.getctime)
    newpic0 = max(glob.iglob('/home/pi/usb/pic/ch0/*.[Jj][Pp][Gg]'), key=os.path.getctime)

    if newpic1 != OldPic1 and newpic0 != OldPic0:
        
        countNoNewpic = 0
        OldPic0 = newpic0    
        OldPic1 = newpic1
        
        with open(newpic1, "rb") as image_file1:
            encoded_string1 = base64.b64encode(image_file1.read())
        with open(newpic0, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            
        data = {'ambulance_id':id,'images_name_1':encoded_string1,'images_name_2':encoded_string}
        try:
            r = requests.post(pic_url, data=data)
            GPIO.output(27,True)
            GPIO.output(17,True)
            countPic += 1
            
            connectionError = 0
        except:
            GPIO.output(27,False)
            connectionError += 1
            if connectionError > 10:
                print "Connection Error"
                break    
            
    else:
        countNoNewpic += 1
      
    if countNoNewpic > 20 :
        GPIO.output(17,False)
        print "No new pic upadte"
        break
      
            
    time.sleep(0.2)
    GPIO.output(17,False)
    if time.time() > timeout:
        print "Timeout"
        print countPic
        break
'''
#GPIO.output(17,False) 
#GPIO.setup(27,False)  
#GPIO.cleanup()