from paho.mqtt import client as mqtt_client
import time
import json
import pymongo
import threading
import time
import subprocess

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
ffmpeg3_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.203/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM1"
ffmpeg4_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.204/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM2"
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

#mosquitto_pub -t "CAR99" -m '{"CAM1":"on","CAM2":"on"}' -u "mqtt" -P "original"

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


def subscribe(client: mqtt_client):
    global currentCAM 
    global p1
    global p2  
    global p3
    global p4
    global ffmpeg1_call
    global ffmpeg2_call
    
    def on_message(client, userdata, msg):
        global currentCAM
        global p1
        global p2  
        global p3
        global p4
        global ffmpeg1_call
        global ffmpeg2_call
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        person_dict = json.loads(msg.payload.decode())

        if((person_dict['CAM1'] == 'on') and (currentCAM['CAM1'] == 'off')):
            
            currentCAM['CAM1'] = 'on'
            currentCAM['TCAM1'] = time.time()
            cmd= ffmpeg1_call.split(' ')
            p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            print("Start Cam1")
            
        elif ((person_dict['CAM1'] == 'off') and (currentCAM['CAM1'] == 'on')):
            currentCAM['CAM1'] = 'off'
            p1.kill()
            print("Stop Cam1")

        if((person_dict['CAM2'] == 'on' ) and (currentCAM['CAM2'] == 'off')):
            currentCAM['CAM2'] = 'on'
            currentCAM['TCAM2'] = time.time()
            cmd= ffmpeg2_call.split(' ')
            p2 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            print("Start Cam2")
            
        elif ((person_dict['CAM2'] == 'off' )and( currentCAM['CAM2'] == 'on')):
            currentCAM['CAM2'] = 'off'
            p2.kill()
            print("Stop Cam2")

    client.subscribe(topic)
    client.on_message = on_message

    print("loop1")
    if(currentCAM['CAM1'] == 'on'):
        print(p1.stderr.readline().rstrip('\r\n'))
        if((time.time() - currentCAM['TCAM1'])  > stremTime  ):
            currentCAM['CAM1'] = 'off'
            p1.kill()
            print("Stop Cam1 time Out")
    if(currentCAM['CAM2'] == 'on'):  
        print(p2.stderr.readline().rstrip('\r\n')) 
        if((time.time() - currentCAM['TCAM2'])  > stremTime  ):
            currentCAM['CAM2'] = 'off'
            p2.kill()
            print("Stop Cam2 time Out")


#p1 = sp.Popen(ffmpeg1_call, stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)


client = connect_mqtt()
subscribe(client)
client.loop_forever()
print("End Loop rtsp")

