#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import os
#os.environ['SDL_AUDIODRIVER'] = 'dsp'
import requests
from gps import *
from time import *
import time
import threading
import RPi.GPIO as GPIO ## Import GPIO library
import json
import pymongo
import subprocess

conn = pymongo.MongoClient()
db = conn.pihos #test is my database
col = db.configs #Here spam is my collection
cur = col.find()  
configs = list(col.find())
print (configs)
conn.close()    

print('Sound > ',configs[0]['soundEn']) # True, False
print('Over_Speed > ' ,configs[0]['speedOver'])
print('Sound_level > ',configs[0]['soundLv']) 
print('speedOverTime > ',configs[0]['speedOverTime']) 

id =  configs[0]['id']
sound = configs[0]['soundEn'] #True#False
sound_level = configs[0]['soundLv']
over_Speed = configs[0]['speedOver']
sound_time_OverSpeed = configs[0]['speedOverTime']

flagOverSpeed = False
timePlaySound = 0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#========For Sound=========
GPIO.setup(23, GPIO.OUT)#sound
GPIO.output(23,False)#disable sound


#import pygame
#pygame.mixer.init()
if(sound_level > 100):
  sound_level = 100
#pygame.mixer.music.set_volume(float(sound_level)/100)
#pygame.mixer.music.load("alert.mp3")
#byteOutput = subprocess.check_output(['aconnect','-x'], timeout=2)
import vlc
player = vlc.MediaPlayer("alert.mp3")
player.audio_set_volume(sound_level)

if(sound == "False"):
    time.sleep(100)
    exit()

gpsd = None #seting the global variable
timeout = None
timeReset = None
threadingOut =  False

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
      if(threadingOut):
        break

gpsp = GpsPoller() # create the thread
gpsp.start() # start it up
countError = 0
timeReset = time.time() + 1200
timestart = time.time()
while True:
  latitude = gpsd.fix.latitude
  speed =  gpsd.fix.speed
  print ('Speed > ',speed , ' ' ,speed*3.6)
  if str(latitude) != 'nan' and str(latitude) != '0.0':
    #print 'GPS Error ', countError , ' setting speed ',over_Speed, 'speed ',str(speed*3.6)
    if(str(speed) != 'nan' and str(speed) != 'NaN'):
        if(int(speed*3.6) > int(over_Speed)):
            if flagOverSpeed == False:
                timePlaySound = time.time()
            flagOverSpeed = True
        else:
            flagOverSpeed = False
            timePlaySound = time.time()

       
        if(flagOverSpeed == True and sound == "True"):
            GPIO.output(23,True)#enable sound
            #print 'Enter Play Sound'
            if(time.time() > timePlaySound+sound_time_OverSpeed):
                #print 'Enter Play Sound with sound'
                
                try:
                    player = vlc.MediaPlayer("alert.mp3")
                    player.play()
                    time.sleep(0.5)
                    duration = player.get_length() / 1000
                    time.sleep(duration - 2)
                    #if(pygame.mixer.music.get_busy() == False):
                    #  pygame.mixer.music.stop()
                    #  time.sleep(0.1)
                    #  pygame.mixer.music.play()
                    #print ('Play Over Speed')
                    #byteOutput = subprocess.check_output(['aconnect','-x'], timeout=2)

                except:
                    print ('Play Sound except')
                #time.sleep(3)
        else:
            GPIO.output(23,False)#disable sound

  

  else:
    countError += 1  

  time.sleep(0.95) #set to whatever
  if time.time() > timeReset:
    print ("TimeReset")
    break
    
  if countError > 20:
    print ("countError")
    break

threadingOut = True
gpsp.running = False
#gpsp.join() # wait for the thread to finish what it's doing
GPIO.output(23,False)#disable sound
GPIO.cleanup()
print ("Done.\nExiting.")
exit()
