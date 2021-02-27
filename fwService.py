import os
import glob
import datetime
import base64
import requests
import time
import sys
import subprocess
import socket

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

#===================================================Update FW Version================================

if internet_on():
    vercurrent = subprocess.check_output('git rev-parse --verify HEAD', shell=True)
    print ("Cur ver " + vercurrent.decode("utf-8") )

    vergit =  subprocess.check_output('git ls-remote https://github.com/izemkung/pihosV4 | head -1 | cut -f 1', shell=True)
    print ('Git ver '+ vergit.decode("utf-8"))
    if vergit == vercurrent :
        print ("version FW Ok!!!")   
        time.sleep(600)
    if (vergit != vercurrent) and (len(vercurrent) == len(vergit)):
        print ("Download FW ")
        if os.path.exists("/home/pi/tmp") == True:
            subprocess.check_output('sudo rm -rf /home/pi/tmp', shell=True)
            time.sleep(5)   
        subprocess.check_output('sudo git clone https://github.com/izemkung/pihosV4 /home/pi/tmp', shell=True)
        time.sleep(10)
        if os.path.exists("/home/pi/pihosV4") == True:
            subprocess.check_output('sudo rm -rf /home/pi/pihosV4', shell=True)
            time.sleep(0.5)
        subprocess.check_output('sudo mv /home/pi/tmp /home/pi/pihosV4', shell=True)
    
        print ("FW Ready to use reboot!!!")
        os.system('sudo mmcli -m 0 -r')
        time.sleep(2)
        os.system('sudo reboot')
else:
    time.sleep(10)
