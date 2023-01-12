from paho.mqtt import client as mqtt_client
import time
import json
import pymongo
import threading
import subprocess
import socket
import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import os
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
apiVersion = configs[0]['apiVersion']
port = 1883
username = configs[0]['mqttUse']
password = configs[0]['mqttPass']
rtspURL = configs[0]['serverRTSP']
numCAM = configs[0]['camN']

ffmpeg1_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.201/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM1"
ffmpeg2_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.202/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM2"
ffmpeg3_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.203/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM3"
ffmpeg4_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.204/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM4"

#ffmpeg1_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.201/ch0_0.h264 -vcodec copy -acodec copy -r 10 -f flv "+ rtspURL +"/"+ topic +"CAM1"
#ffmpeg2_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.202/ch0_0.h264 -vcodec copy -acodec copy -r 10 -f flv "+ rtspURL +"/"+ topic +"CAM2"
#ffmpeg3_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.203/ch0_0.h264 -vcodec copy -acodec copy -r 10 -f flv "+ rtspURL +"/"+ topic +"CAM3"
#ffmpeg4_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.204/ch0_0.h264 -vcodec copy -acodec copy -r 10 -f flv "+ rtspURL +"/"+ topic +"CAM4"

currentCAM = {}
currentCAM['CAM1'] = 'off'
currentCAM['CAM2'] = 'off'
currentCAM['CAM3'] = 'off'
currentCAM['CAM4'] = 'off'
currentCAM['TCAM1'] =  time.time()
currentCAM['TCAM2'] =  time.time()
currentCAM['TCAM3'] =  time.time()
currentCAM['TCAM4'] =  time.time()

hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204']
CamOnline = [False,False,False,False]

p1 = 0
p2 = 0    
p3 = 0
p4 = 0

print( 'Strem Clien Ver > ' , apiVersion)
print( 'Subscribe topic > ' , topic)
client_id = 'python-mqtt-'+ configs[0]['sn']
print( 'Mqtt Client_id  > ' , client_id)
print( 'Camera num      > ' , numCAM)


person_string = '{"CAM1" : "off" ,"CAM2" : "off" ,"CAM3" : "off"  ,"CAM4" : "off"}'
person_dict = json.loads(person_string)
print(json.dumps(person_dict, indent = 4, sort_keys=True))
jsonCmd = person_dict
print(jsonCmd)

rtsp = None
threadingOut = False 

REMOTE_SERVER = "www.google.com"
#mosquitto_pub -t "CAR99" -m '{"CAM1":"on","CAM2":"on"}' -u "mqtt" -P "original"
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
    return client


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0


def subscribe(client: mqtt_client):
    global currentCAM 
    global p1
    global p2  
    global p3
    global p4
    global ffmpeg1_call
    global ffmpeg2_call
    global ffmpeg3_call
    global ffmpeg4_call
    global person_dict
    global rtsp
    
    def on_message(client, userdata, msg):
        global currentCAM
        global p1
        global p2  
        global p3
        global p4
        global ffmpeg1_call
        global ffmpeg2_call
        global ffmpeg3_call
        global ffmpeg4_call
        global person_dict
        global rtsp
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        jsonIN = json.loads(msg.payload.decode())

        if jsonIN.get('CAM1') != None:
            person_dict['CAM1'] = jsonIN['CAM1']
        if jsonIN.get('CAM2') != None:
            person_dict['CAM2'] = jsonIN['CAM2']
        if jsonIN.get('CAM3') != None:
            person_dict['CAM3'] = jsonIN['CAM3']
        if jsonIN.get('CAM4') != None:
            person_dict['CAM4'] = jsonIN['CAM4']

        if jsonIN.get('RESET') != None:
            
            ret = client.publish(publshTopic, topic + " reset") 
            os.system('sudo reboot')


        #person_dict = jsonIN
        

        print(rtsp.is_alive())
        if rtsp.is_alive() == False:
            rtsp.terminate()  
            rtsp = rtspPoller()
            rtsp.start()

    client.subscribe(topic)
    client.on_message = on_message



class rtspPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global currentCAM
    global p1
    global p2  
    global p3
    global p4
    global ffmpeg1_call
    global ffmpeg2_call
    global ffmpeg3_call
    global ffmpeg4_call
    global person_dict
    global threadingOut
    global rtsp
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global currentCAM
    global p1
    global p2  
    global p3
    global p4
    global ffmpeg1_call
    global ffmpeg2_call
    global ffmpeg3_call
    global ffmpeg4_call
    global person_dict
    global threadingOut
    global rtsp
    oldline1 = ""
    oldline2 = ""
    oldline3 = ""
    oldline4 = ""
    line1 = ""
    line2 = ""
    line3 = ""
    line4 = ""
    while rtsp.running:
        time.sleep(0.1)
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

        if((person_dict['CAM3'] == 'on' ) and (currentCAM['CAM3'] == 'off')):
            
            currentCAM['CAM3'] = 'on'
            currentCAM['TCAM3'] = time.time()
            cmd= ffmpeg3_call.split(' ')
            p3 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            print("Start Cam3")
            
        elif ((person_dict['CAM3'] == 'off' )and( currentCAM['CAM3'] == 'on')):
           
            currentCAM['CAM3'] = 'off'
            p3.kill()
            print("Stop Cam3")
        
        if((person_dict['CAM4'] == 'on' ) and (currentCAM['CAM4'] == 'off')):
            
            currentCAM['CAM4'] = 'on'
            currentCAM['TCAM4'] = time.time()
            cmd= ffmpeg4_call.split(' ')
            p4 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            print("Start Cam4")
            
        elif ((person_dict['CAM4'] == 'off' )and( currentCAM['CAM4'] == 'on')):
            
            currentCAM['CAM4'] = 'off'
            p4.kill()
            print("Stop Cam4")

#==============================================================================
        if (currentCAM['CAM1'] == 'on'):
            line1 = p1.stdout.readline().rstrip('\r\n')
            if line1 == "" and p1.poll() is not None:
                currentCAM['CAM1'] = 'off'
                returncode = p1.returncode
                
                if returncode == 0:
                    # ffmpeg has successfully exited
                    end = time.time()
                    print('CAM1 > ffmpeg cam1 completed in {}'.format(strftime('%H:%M:%S', time.gmtime(end - start))))
                else:
                    print('CAM1 > ffmpeg cam1 has terminated with code '+ str(p1.returncode))     
            if line1 != oldline1:
                print('CAM1 > '+ line1)

            if((time.time() - currentCAM['TCAM1'])  > stremTime  ):
                currentCAM['CAM1'] = 'off'
                p1.kill()
                print("CAM1 > Stop Cam1 time Out")

        if (currentCAM['CAM2'] == 'on'):
            line2 = p2.stdout.readline().rstrip('\r\n')
            if line2 == "" and p2.poll() is not None:
                currentCAM['CAM2'] = 'off'
                returncode = p2.returncode
                if returncode == 0:
                    # ffmpeg has successfully exited
                    end = time.time()
                    print('CAM2 > ffmpeg cam2 completed in {}'.format(strftime('%H:%M:%S', time.gmtime(end - start))))
                else:
                    print('CAM2 > ffmpeg cam2 has terminated with code '+ str(p2.returncode))     
            if line2 != oldline2:
                print('CAM2 > '+ line1)

            if((time.time() - currentCAM['TCAM2'])  > stremTime  ):
                currentCAM['CAM2'] = 'off'
                p2.kill()
                print("CAM2 > Stop Cam2 time Out")

        if (currentCAM['CAM3'] == 'on'):
            line3 = p3.stdout.readline().rstrip('\r\n')
            if line3 == "" and p3.poll() is not None:
                currentCAM['CAM3'] = 'off'
                returncode = p3.returncode
                if returncode == 0:
                    # ffmpeg has successfully exited
                    end = time.time()
                    print('CAM3 > ffmpeg cam3 completed in {}'.format(strftime('%H:%M:%S', time.gmtime(end - start))))
                else:
                    print('CAM3 > ffmpeg cam3 has terminated with code '+ str(p3.returncode))     
            if line3 != oldline3:
                print('CAM3 > '+ line3)

            if((time.time() - currentCAM['TCAM3'])  > stremTime  ):
                currentCAM['CAM3'] = 'off'
                p3.kill()
                print("CAM3 > Stop Cam3 time Out")

        if (currentCAM['CAM4'] == 'on'):
            line4 = p4.stdout.readline().rstrip('\r\n')
            if line4 == "" and p4.poll() is not None:
                currentCAM['CAM4'] = 'off'
                returncode = p4.returncode
                if returncode == 0:
                    # ffmpeg has successfully exited
                    end = time.time()
                    print('CAM4 > ffmpeg cam4 completed in {}'.format(strftime('%H:%M:%S', time.gmtime(end - start))))
                else:
                    print('CAM4 > ffmpeg cam4 has terminated with code '+ str(p4.returncode))     
            if line4 != oldline4:
                print('CAM4 > '+ line4)

            if((time.time() - currentCAM['TCAM4'])  > stremTime  ):
                currentCAM['CAM4'] = 'off'
                p4.kill()
                print("CAM4 > Stop Cam4 time Out")

        if(threadingOut):
            if p1.poll() is not None: 
                p1.kill()
            if p2.poll() is not None: 
                p2.kill()
            if p3.poll() is not None: 
                p3.kill()
            if p4.poll() is not None: 
                p4.kill()
            break

    print("End thread")
    rtsp.running = False


#p1 = sp.Popen(ffmpeg1_call, stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)
while(internet_on() == False):
    time.sleep(20)


rtsp = rtspPoller()
rtsp.start()



if(apiVersion != 3):
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()
    print("RTSP Start by MQTT")


countCamOnline = 0
startCheckTime = time.time()
if(apiVersion == 3):
    print("RTSP Start Auto")
    while(True):
        time.sleep(20)
        countCamOnline = 0

        for x in range(numCAM):
            print('Ping CAM',x+1)
            if (ping(hosts[x]) == True):
                print('Find CAM',x+1)
                countCamOnline += 1
                CamOnline[x] = True
            else :
                CamOnline[x] = False

        if((time.time() - startCheckTime ) > stremTime-5):
            print("Time Out CAM N " , numCAM )
            threadingOut = True
            break
        
        time.sleep(20)

        person_dict['CAM1'] = ('on' if CamOnline[0] == True else 'off')
        person_dict['CAM2'] = ('on' if CamOnline[1] == True else 'off')
        person_dict['CAM3'] = ('on' if CamOnline[2] == True else 'off')
        person_dict['CAM4'] = ('on' if CamOnline[3] == True else 'off')

        
        print(person_dict)
    

threadingOut = True
rtsp.running = False
print("End Loop rtsp")

