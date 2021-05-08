from paho.mqtt import client as mqtt_client
import time
import json
import pymongo
import threading
import time
import subprocess
import socket

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

while(internet_on() == False):
    time.sleep(20)

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    print("loop2")
    return client
    
# generate client ID with pub prefix randomly
conn = pymongo.MongoClient()
db = conn.pihos #test is my database
col = db.configs #Here spam is my collection
cur = col.find()  
configs = list(col.find())
print (configs)
conn.close() 

topic = 'CAR'+configs[0]['id']
stremTime = configs[0]['timeRTSP']
broker = configs[0]['mqtt']
port = 1883
username = configs[0]['mqttUse']
password = configs[0]['mqttPass']
rtspURL = configs[0]['serverRTSP']

ffmpeg1_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.201/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM1"
ffmpeg2_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.202/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM2"
ffmpeg3_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.203/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM3"
ffmpeg4_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.204/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM4"
currentCAM = {}
currentCAM['CAM1'] = 'off'
currentCAM['CAM2'] = 'off'
currentCAM['CAM3'] = 'off'
currentCAM['CAM4'] = 'off'
currentCAM['TCAM1'] =  time.time()
currentCAM['TCAM2'] =  time.time()
currentCAM['TCAM3'] =  time.time()
currentCAM['TCAM4'] =  time.time()

p1 = 0
p2 = 0    
p3 = 0
p4 = 0

print( 'Subscribe topic > ' , topic)

client_id = 'python-mqtt-'+ configs[0]['sn']

person_string = '{"CAM1" : "on" ,"CAM2" : "on"}'
person_dict = json.loads(person_string)
print(json.dumps(person_dict, indent = 4, sort_keys=True))
jsonCmd = person_dict
print(jsonCmd)
print(jsonCmd['CAM1'])
print(jsonCmd['CAM2'])

cmd= ffmpeg1_call.split(' ')
p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True) 

print("Loop") 
oldline1 = ""
oldline2 = ""
oldline3 = ""
oldline4 = ""
line1 = ""
line2 = ""
line3 = ""
line4 = ""

while(True):
    time.sleep(0.1)
    #line = p1.stdout.readline().strip() 
    line1 = p1.stdout.readline().rstrip('\r\n')
    if line1 == "" and p1.poll() is not None:
        returncode = p1.returncode
        if returncode == 0:
            # ffmpeg has successfully exited
            end = time.time()
            print('ffmpeg cam1 completed in {}'.format(strftime('%H:%M:%S', time.gmtime(end - start))))
        else:
            print('ffmpeg cam1 has terminated with code '+p1.returncode)

        break

    if line != oldline:
        print(line)

    oldline = line 


p1.kill()
print("End Loop rtsp")

