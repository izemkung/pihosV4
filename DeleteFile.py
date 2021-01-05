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
import sys
import subprocess

#===================================================Update FW Version================================
vercurrent = subprocess.check_output('git rev-parse --verify HEAD', shell=True)
print 'Cur ver ' + vercurrent

vergit =  subprocess.check_output('git ls-remote https://github.com/izemkung/pihos2 | head -1 | cut -f 1', shell=True)
print 'Git ver '+ vergit
if vergit == vercurrent :
    print "version FW Ok!!!"   
if vergit != vercurrent and len(vercurrent) == len(vergit):
    print "Download FW "
    if os.path.exists("/home/pi/tmp") == True:
        print subprocess.check_output('sudo rm -rf /home/pi/tmp', shell=True) 
        time.sleep(5)   
    print subprocess.check_output('sudo git clone https://github.com/izemkung/pihos2 /home/pi/tmp', shell=True)
    time.sleep(10)
    if os.path.exists("/home/pi/tmp") == True:
        print subprocess.check_output('sudo rm -rf /home/pi/pihos', shell=True)
        #time.sleep(10)
        print subprocess.check_output('sudo mv /home/pi/tmp /home/pi/pihos', shell=True)
   
    print "FW Ready to use!!!"
    os.system('sudo reboot')
