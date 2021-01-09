#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import sys
print("Python version")
print (sys.version)
print("Version info.")
print (sys.version_info)

import os
import requests
from gps import *
from time import *
import time
import threading
import RPi.GPIO as GPIO ## Import GPIO library
import serial
import time
import json
import socket

import pymongo
conn = pymongo.MongoClient()
db = conn.pihos #test is my database
col = db.configs #Here spam is my collection
cur = col.find()  
configs = list(col.find())
print (configs)
conn.close()
#array = json.loads(array)

print(configs[0]['id'])
print(configs[0]['server'])
id =  configs[0]['id']

gps_url = configs[0]['server'] + ":3020/api/gps"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

gpsd = None 
threadingOut = False 
timeout = None
timeReset = None
gpsStatus = 'gps'

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

def GpsStatus(var):
  global gpsStatus
  if (var == gpsStatus):
    return
  gpsStatus = var
  mongoConn = pymongo.MongoClient()
  db_pihos = mongoConn.pihos #test is my database
  db_pihos_status = db_pihos.status
  newvalues = {}
  newvalues['statusGPS'] = var
  newvalues = { "$set": newvalues}
  db_pihos_status.update_one({}, newvalues)
  mongoConn.close()

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

while(internet_on() == False):
    time.sleep(10)
    
print ('URL > ',gps_url,' ID > ',id)
gpsp = GpsPoller() # create the thread

GPIO.setup(22, GPIO.OUT)#GPS

gpsp.start() # start it up
countSend = 0
countError = 0
timeout = time.time() + 120


while True:
 
  print ('GPS sending Seccess ' , countSend ,' Error ', countError ) 
 
  if (str(gpsd.fix.latitude) != 'nan' and str(gpsd.fix.latitude) != '0.0'):
    GPIO.output(22,True)
    try:
      resp = requests.get(gps_url+'/?ambulance_id={0}&tracking_latitude={1:.6f}&tracking_longitude={2:.6f}&tracking_speed={3:.2f}&tracking_heading={4}'.format(id,gpsd.fix.latitude,gpsd.fix.longitude,gpsd.fix.speed,gpsd.fix.track),timeout=(2.05, 5))
      
      if(resp.status_code != 200 ):
        print ('status_code ' , resp.status_code)
        time.sleep(0.3)
        GPIO.output(22,False)
        GpsStatus('code : ' + resp.status_code)
        timeout = time.time() + 10
      #print 'headers     ' , resp.headers
      #print 'content     ' , resp.content
      #GPIO.output(27,True)
      if(resp.status_code == 200 ):
        
        countSend += 1
        countError = 0
        timeout = time.time() + 60 #timeout reset
        GpsStatus('up')
      else:
        print ('respError')
        countError += 1

    except:
      print ('exceptError')
      countError += 1
      time.sleep(0.5) #set to whatever
      GPIO.output(22,False)
  else:
    countError += 1  
  
  #time.sleep(0.2) #set to whatever
  GPIO.output(22,False)
  time.sleep(0.95) #set to whatever

  if (time.time() > timeout):
    print ("Timeout")
    GpsStatus('Timeout')
    for count in range(0, 2):
      time.sleep(0.5)
      GPIO.output(22,True)
      time.sleep(2)
      GPIO.output(22,False)
    break
    
  if (countError > 30):
    GpsStatus('countError')
    print ("countError")
    for count in range(0, 10):
      time.sleep(0.2)
      GPIO.output(22,True)
      time.sleep(0.2)
      GPIO.output(22,False)
    break

threadingOut = True
gpsp.running = False
gpsp.join() # wait for the thread to finish what it's doing
GPIO.output(22,False)
GPIO.cleanup()
print ("Done.\nExiting.")
exit()

  #print 'altitude (m)' , gpsd.fix.altitude
    #print 'eps         ' , gpsd.fix.eps
    #print 'epx         ' , gpsd.fix.epx
    #print 'epv         ' , gpsd.fix.epv
    #print 'ept         ' , gpsd.fix.ept
    #print 'speed (m/s) ' , gpsd.fix.speed
    #print 'climb       ' , gpsd.fix.climb
    #print 'track       ' , gpsd.fix.track
    #print 'mode        ' , gpsd.fix.mode
    #print
    #print 'sats        ' , gpsd.satellites
    
  
  #r = urllib.request.urlopen('https://api.github.com', auth=('user', 'pass'))
  #var r = requests.get('http://www.google.com')
  
    

#except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
  #print "\nKilling Thread..."
  #gpsp.running = False
  #gpsp.join() # wait for the thread to finish what it's doing
  #GPIO.output(27,False)
  #GPIO.output(22,False)
  #GPIO.cleanup()
  #exit()



